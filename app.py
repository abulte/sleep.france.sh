from datetime import date, timedelta

from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, url_for, session, redirect, request
from werkzeug.exceptions import NotFound

from models import Day, init_app as init_models
from cli import bp as cli_bp

app = Flask(__name__)
app.config.from_pyfile("settings.py")

oauth = OAuth(app)
oauth.register("garmin", fetch_token=lambda: session.get("token"))

init_models(app)
app.register_blueprint(cli_bp)


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


# FIXME: custom url converter
@app.route("/day/<day>", methods=["GET", "POST"])
def day_view(day):
    try:
        day = date.fromisoformat(day)
    except ValueError:
        raise NotFound

    # FIXME: model fn
    try:
        day = Day.get(date=day)
    except Day.DoesNotExist:
        day = Day(date=day)

    if request.method == "POST":
        # save "proxy" Day if needed
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

    return render_template("day.html", day=day)


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
    # FIXME: there's a -1 day delta here I don't understand
    # (should be in [6, 7] in iso and works in shell)
    if day.vacation is None and day.date.isoweekday() in [5, 6]:
        return True
    return day.vacation
