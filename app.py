from datetime import date, timedelta, datetime

from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, url_for, session, redirect, request
from flask_security import Security

from cli import bp as cli_bp
from models import Day, Sleep, init_app as init_models
from utils import ISODateConverter

app = Flask(__name__)
app.config.from_pyfile("settings.py")

oauth = OAuth(app)
oauth.register("garmin", fetch_token=lambda: session.get("token"))

init_models(app)
security = Security(app, app.user_datastore)
app.register_blueprint(cli_bp)

app.url_map.converters["isodate"] = ISODateConverter


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/legal")
def legal():
    return render_template("legal.html")


@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return oauth.garmin.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    token = oauth.garmin.authorize_access_token()
    # FIXME:
    session["token"] = token
    # do something with the token and profile
    return redirect("/")


@app.route("/day/today")
def today():
    return redirect(url_for("day_view", day=date.today().isoformat()))


@app.route("/day/<isodate:day>", methods=["GET", "POST"])
def day_view(day):
    day = Day.get_or_create(day)

    if request.method == "POST":
        # save "proxy" freshly created Day if needed
        if day.is_dirty():
            day.save()
        kwargs = {
            "notes": request.form.get("notes"),
            "alcohol_doses": request.form.get("alcohol_doses"),
            "mood": request.form.get("mood"),
            "tiredness_morning": request.form.get("tiredness_morning"),
            "tiredness_evening": request.form.get("tiredness_evening"),
            "nap_minutes": request.form.get("nap_minutes"),
            "office": request.form.get("office") == "yes",
            "vacation": request.form.get("vacation") == "yes",
        }
        Day.update(**kwargs).where(Day.id == day.id).execute()
        return redirect(request.url)

    return render_template("day.html", day=day, today=date.today())


@app.route("/api/sleep/garmin", methods=["POST"])
def api_sleep_garmin():
    data = request.json
    if not data or not data.get("sleeps"):
        app.logger.error(f"Malformed data: {request.text}")
        return "No sleeps json found", 400

    # TODO: link to user first (through token?)

    for sleep in data["sleeps"]:
        day = sleep["calendarDate"]
        day = Day.get_or_create(day, autosave=True)
        try:
            start = datetime.fromtimestamp(sleep["startTimeInSeconds"])
            end = start + timedelta(seconds=sleep["durationInSeconds"])
            kwargs = {
                "duration_total":  sleep["durationInSeconds"],
                "duration_rem":  sleep["remSleepInSeconds"],
                "duration_deep":  sleep["deepSleepDurationInSeconds"],
                "duration_awake":  sleep["awakeDurationInSeconds"],
                "phases":  sleep["sleepLevelsMap"],
                "start":  start,
                "end":  end,
                "offset": sleep["startTimeOffsetInSeconds"],
            }
        except ValueError as e:
            app.logger.error(f"Missing data: {e}")
            return "Missing data", 400
        else:
            sleep_obj = Sleep.create_or_update(day, kwargs)
            app.logger.debug(f"Updated sleep {sleep_obj.id}")

    return "ok", 200


@app.template_filter('datedelta')
def datedelta(value, delta):
    return value + timedelta(days=delta)


@app.template_filter('is_vacation')
def is_vacation(day):
    """
    Vacation when:
    - explicitely set
    - by default, when weekend
    Else, not.
    """
    if day.vacation is None and day.date.isoweekday() in [6, 7]:
        return True
    return day.vacation
