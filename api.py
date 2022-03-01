from datetime import datetime, timedelta

from flask import Blueprint, request, current_app, jsonify, url_for
from flask_security import auth_required
from playhouse.shortcuts import model_to_dict
from playhouse.flask_utils import get_object_or_404
from pytz import timezone, utc

from models import Sleep, User, Day, Stress


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/sleep/garmin", methods=["POST"])
def api_sleep_garmin():
    data = request.json
    if not data or not data.get("sleeps"):
        current_app.logger.error(f"Malformed data: {request.text}")
        return "No sleeps json found", 400

    for sleep in data["sleeps"]:
        try:
            user = User.get(
                User.token["garmin"]["oauth_token"] == sleep["userAccessToken"]
            )
        except (User.DoesNotExist, KeyError):
            current_app.logger.error(f"No user found for sleep {sleep}")
            continue
        # FIXME: use those w/o calendarDate too? apparently they're not daily and have different values
        # maybe triggered by enabling stress endpoint (since they are stress values in there)
        # cf `data/non-daily-sleep-payload.json`
        if not sleep.get("calendarDate"):
            current_app.logger.info("Ignoring sleep payload w/o calendarDate: {sleep}")
            continue
        try:
            day = Day.get_or_create(sleep["calendarDate"], user, autosave=True)
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
        except KeyError as e:
            current_app.logger.error(f"Missing data: {e} — {sleep}")
            return "Missing data", 400
        else:
            sleep_obj = Sleep.create_or_update(day, "garmin", kwargs)
            current_app.logger.debug(f"Updated sleep {sleep_obj.id}")

    return "thanks :-)", 200


@bp.route("/stress/garmin", methods=["POST"])
def api_stress_garmin():
    data = request.json
    if not data or not data.get("stressDetails"):
        current_app.logger.error(f"Malformed data: {request.json}")
        return "No stress json found", 400

    for stress in data["stressDetails"]:
        try:
            user = User.get(
                User.token["garmin"]["oauth_token"] == stress["userAccessToken"]
            )
        except (User.DoesNotExist, KeyError):
            current_app.logger.error(f"No user found for stress {stress}")
            continue
        # FIXME: check if we have those for stress
        if not stress.get("calendarDate"):
            current_app.logger.info("Ignoring stress payload w/o calendarDate: {sleep}")
            continue
        try:
            day = Day.get_or_create(stress["calendarDate"], user, autosave=True)
            start = datetime.fromtimestamp(stress["startTimeInSeconds"])
            end = start + timedelta(seconds=stress["durationInSeconds"])
            kwargs = {
                "duration_total":  stress["durationInSeconds"],
                "start":  start,
                "end":  end,
                "offset": stress["startTimeOffsetInSeconds"],
            }
            if stress_values := stress.get("timeOffsetStressLevelValues"):
                kwargs["stress_values"] = stress_values
            if battery_values := stress.get("timeOffsetBodyBatteryValues"):
                kwargs["battery_values"] = battery_values
        except KeyError as e:
            current_app.logger.error(f"Missing data: {e} — {stress}")
            return "Missing data", 400
        else:
            stress_obj = Stress.create_or_update(day, kwargs)
            current_app.logger.debug(f"Updated stress {stress_obj.id}")

    return "thanks :-)", 200


def api_sleep_withings():
    """Not a real route, called from oauth.authorize for `notify` pattern"""
    # circular dep (sorry)
    from oauth import session_for_user
    user_id = request.form["userid"]
    start = request.form["startdate"]
    end = request.form["enddate"]
    user = User.get(User.token["withings"]["userid"] == user_id)

    with session_for_user(user) as _oauth:
        r = _oauth.withings.post("v2/sleep", data={
            "action": "getsummary",
            "lastupdate": start,
        })
        r_details = _oauth.withings.post("v2/sleep", data={
            "startdate": start,
            "enddate": end,
            "action": "get",
        })
        r.raise_for_status()
        r_details.raise_for_status()

    # cf `withings-sleep-summary-payload.json`
    data = r.json()
    if data.get("status") != 0:
        raise Exception(f"api_sleep_withings(summary) went wrong: {data}")

    # cf `withings-sleep-details-payload.json`
    details = r_details.json()
    if details.get("status") != 0:
        raise Exception(f"api_sleep_withings(details) went wrong: {details}")

    for serie in data.get("body", {}).get("series", []):
        day = Day.get_or_create(serie["date"], user, autosave=True)
        tz = timezone(serie["timezone"])
        start = datetime.fromtimestamp(serie["startdate"], tz=tz)
        end = datetime.fromtimestamp(serie["enddate"], tz=tz)
        kwargs = {
            "duration_total":  serie["data"]["total_timeinbed"],
            "duration_rem":  serie["data"]["remsleepduration"],
            "duration_deep":  serie["data"]["deepsleepduration"],
            "duration_awake":  serie["data"]["wakeupduration"],
            "start": start.astimezone(utc),
            "end": end.astimezone(utc),
            "offset": start.utcoffset().seconds,
            # we better _hope_ this is associated to the same date
            "phases": details.get("body", {}).get("series", []),
        }
        sleep_obj = Sleep.create_or_update(day, "withings", kwargs)
        current_app.logger.debug(f"Updated sleep {sleep_obj.id}")

    return "ok", 200


@auth_required
@bp.route("/calendar")
def calendar():
    """Calendar data for a given timespan and data type"""
    cal = request.args["calendar"]
    start = datetime.fromisoformat(request.args["start"]).astimezone(utc)
    end = datetime.fromisoformat(request.args["end"]).astimezone(utc)
    days = Day.select().where(
        Day.date >= start,
        Day.date < end + timedelta(days=1)
    )

    data = {}
    if cal == "sleep":
        data = [{
            "id": f"sleep-{d.date}",
            "start": d.date.isoformat(),
            "title": f"😴 {d.sleep_score()}",
            "value": d.sleep_score(),
            "url": url_for("day_summary", day=d.date),
        } for d in days if d.sleeps]
    elif cal == "stress":
        data = [{
            "id": f"stress-{d.date}",
            "start": d.date.isoformat(),
            "title": f"⚡️ {d.battery_score()}",
            "value": d.battery_score(),
            "url": url_for("day_summary", day=d.date),
        } for d in days if d.stresses]
    elif cal == "mood":
        data = [{
            "id": f"mood-{d.date}",
            "start": d.date.isoformat(),
            "title": "📝 Journal",
            "url": url_for("day_view", day=d.date),
        } for d in days if d.tiredness_morning]

    return jsonify(data)


def serialize_day(day):
    return model_to_dict(day, backrefs=True, exclude=(Day.user, ))


@auth_required
@bp.route("/day/<isodate:day>")
def day_api(day):
    day = get_object_or_404(Day, (Day.date == day))
    return jsonify(serialize_day(day))


@auth_required
@bp.route("/days")
def days_api():
    start = datetime.fromisoformat(request.args["start"]).astimezone(utc)
    end = datetime.fromisoformat(request.args["end"]).astimezone(utc)
    days = Day.select().where(
        Day.date >= start,
        Day.date < end + timedelta(days=1)
    )
    return jsonify([serialize_day(d) for d in days])
