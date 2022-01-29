from flask import Blueprint, current_app

import models

bp = Blueprint("cli", __name__, cli_group=None)


@bp.cli.command("init-db")
def init_db():
    models.init_db()


@bp.cli.command("backfill")
def backfill():
    current_app.oauth.garmin.get("backfill/sleeps")
