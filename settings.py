import os

SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

GARMIN_CLIENT_ID = os.environ.get("GARMIN_CLIENT_ID")
GARMIN_CLIENT_SECRET = os.environ.get("GARMIN_CLIENT_SECRET")
GARMIN_REQUEST_TOKEN_URL = "https://connectapi.garmin.com/oauth-service/oauth/request_token"  # noqa
GARMIN_AUTHORIZE_URL = "https://connect.garmin.com/oauthConfirm"
GARMIN_ACCESS_TOKEN_URL = "https://connectapi.garmin.com/oauth-service/oauth/access_token"  # noqa
# GARMIN_API_BASE_URL = "https://connectapi.garmin.com/oauth-service/oauth/access_token"  # noqa
