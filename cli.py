import click

from flask import Blueprint, current_app
from flask_security import hash_password

import models

bp = Blueprint("cli", __name__, cli_group=None)


@bp.cli.command("init-db")
def init_db():
    models.init_db()


@bp.cli.command("create-user")
@click.argument("email")
@click.argument("password")
def create_user(email, password):
    ds = current_app.user_datastore
    if not ds.find_user(email=email):
        ds.create_user(email=email, password=hash_password(password))
        print("User created.")
