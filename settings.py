import os

SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")
DATABASE = os.environ.get("DATABASE_URL")

SECURITY_PASSWORD_SALT = os.environ.get("FLASK_SECRET_KEY")

GARMIN_CLIENT_ID = os.environ.get("GARMIN_CLIENT_ID")
GARMIN_CLIENT_SECRET = os.environ.get("GARMIN_CLIENT_SECRET")
GARMIN_REQUEST_TOKEN_URL = "https://connectapi.garmin.com/oauth-service/oauth/request_token"  # noqa
GARMIN_AUTHORIZE_URL = "https://connect.garmin.com/oauthConfirm"
GARMIN_ACCESS_TOKEN_URL = "https://connectapi.garmin.com/oauth-service/oauth/access_token"  # noqa
GARMIN_API_BASE_URL = "https://apis.garmin.com/wellness-api/rest/"  # noqa

WITHINGS_CLIENT_ID = os.environ.get("WITHINGS_CLIENT_ID")
WITHINGS_CLIENT_SECRET = os.environ.get("WITHINGS_CLIENT_SECRET")
WITHINGS_AUTHORIZE_URL = "https://account.withings.com/oauth2_user/authorize2"
WITHINGS_AUTHORIZE_PARAMS = {
    "scope": "user.activity",
}
WITHINGS_ACCESS_TOKEN_URL = "https://account.withings.com/oauth2/token"  # noqa
WITHINGS_API_BASE_URL = "https://wbsapi.withings.net/v2/"
