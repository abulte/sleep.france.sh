from flask import Blueprint

import models

bp = Blueprint("cli", __name__, cli_group=None)


@bp.cli.command("init-db")
def init_db():
    models.init_db()
