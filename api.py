from datetime import datetime, timedelta

from flask import Blueprint, request, current_app

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
        except (User.DoesNotExist, ValueError):
            current_app.logger.error(f"No user found for sleep {sleep}")
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
        except ValueError as e:
            current_app.logger.error(f"Missing data: {e}")
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
        except (User.DoesNotExist, ValueError):
            current_app.logger.error(f"No user found for stress {stress}")
            continue
        try:
            day = Day.get_or_create(stress["calendarDate"], user, autosave=True)
            start = datetime.fromtimestamp(stress["startTimeInSeconds"])
            end = start + timedelta(seconds=stress["durationInSeconds"])
            kwargs = {
                "duration_total":  stress["durationInSeconds"],
                "stress_values": stress["timeOffsetStressLevelValues"],
                "battery_values": stress["timeOffsetBodyBatteryValues"],
                "start":  start,
                "end":  end,
                "offset": stress["startTimeOffsetInSeconds"],
            }
        except ValueError as e:
            current_app.logger.error(f"Missing data: {e}")
            return "Missing data", 400
        else:
            stress_obj = Stress.create_or_update(day, kwargs)
            current_app.logger.debug(f"Updated stress {stress_obj.id}")

    return "thanks :-)", 200
