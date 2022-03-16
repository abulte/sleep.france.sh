import requests

from contextlib import contextmanager

from authlib.common.urls import add_params_to_qs
from authlib.integrations.base_client import InvalidTokenError
from authlib.integrations.flask_client import OAuth
from flask import Blueprint, current_app, url_for, redirect, request
from flask_security import auth_required, current_user

from api import api_sleep_withings
from models import User


bp = Blueprint("oauth", __name__, url_prefix="")
oauth = OAuth()


def token_update(provider, token, refresh_token=None, access_token=None):
    current_app.logger.debug(f"on_token_update: {provider} {token}")

    # FIXME: ugly code duplication
    if refresh_token:
        try:
            user = User.get(User.token[provider]["refresh_token"] == refresh_token)
        except User.DoesNotExist:
            current_app.logger.error(f"Failed token refresh for {provider}: {refresh_token}")
            raise InvalidTokenError()
    elif access_token:
        try:
            user = User.get(User.token[provider]["access_token"] == access_token)
        except User.DoesNotExist:
            current_app.logger.error(f"Failed token update for {provider}: {access_token}")
            raise InvalidTokenError()
    else:
        return

    # update old token
    user.token[provider] = token
    user.save()
    current_app.logger.debug("Token updated!")


def token_update_withings(*args, **kwargs):
    token_update("withings", *args, **kwargs)


def get_withings_client_params(kwargs={}):
    """This needs to be injected to withings API for
    - access token request
    - refresh token request
    """
    kwargs.update({
        "client_id": current_app.config["WITHINGS_CLIENT_ID"],
        "client_secret": current_app.config["WITHINGS_CLIENT_SECRET"],
    })
    return kwargs


def compliance_fix(session):
    def inject_client_params(url, headers, data):
        data = add_params_to_qs(data, get_withings_client_params({"action": "requesttoken"}))
        return url, headers, data

    def debug_token_response(response):
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            current_app.logger.error(f"token_response error: {e} {response.text}")
            raise e
        return response

    def format_token_response(response):
        response = debug_token_response(response)
        data = response.json()["body"]
        response.json = lambda: data
        return response

    session.register_compliance_hook("refresh_token_request", inject_client_params)
    session.register_compliance_hook("refresh_token_response", format_token_response)
    session.register_compliance_hook("access_token_response", format_token_response)


@bp.route("/login/<provider>")
@auth_required()
def login_oauth(provider):
    redirect_uri = url_for("oauth.authorize", provider=provider, _external=True)
    return getattr(oauth, provider).authorize_redirect(redirect_uri)


@bp.route("/authorize/<provider>")
@auth_required()
def authorize(provider):
    kwargs = get_withings_client_params({"action": "requesttoken"}) \
        if provider == "withings" else {}
    token = getattr(oauth, provider).authorize_access_token(**kwargs)
    current_app.logger.debug(f"Got authorize token: {token}")
    has_previous_token = current_user.token.get("withings")
    current_user.token[provider] = token
    current_user.save()
    if not has_previous_token and provider == "withings":
        subscribe_withings()
    return redirect(url_for("account"))


@bp.route("/authorize/withings", methods=["POST"])
def withings_notify():
    """Crazy withings API uses this endpoint for notifications..."""
    current_app.logger.debug(f"Received withings notification: {request.args}")
    return api_sleep_withings()


def subscribe_withings():
    r = oauth.withings.post("notify", data={
        "action": "subscribe",
        "callbackurl": url_for("oauth.authorize", provider="withings", action="notify", _external=True),
        # sleep activity
        "appli": 44,
    })
    r.raise_for_status()
    current_app.logger.debug(f"Subscribed to withings updates: {r.json()}")


@contextmanager
def session_for_user(user, provider="withings"):
    """Hack to act on behalf of a user outside of user's navigation context"""
    _previous_fetch = getattr(oauth, provider)._fetch_token
    try:
        getattr(oauth, provider)._fetch_token = lambda: user.token[provider]
        yield oauth
    finally:
        getattr(oauth, provider)._fetch_token = _previous_fetch


def init_app(app):
    oauth.init_app(app, fetch_token=User.fetch_token)
    oauth.register("garmin")
    oauth.register("withings", compliance_fix=compliance_fix, update_token=token_update_withings)
    app.register_blueprint(bp)
