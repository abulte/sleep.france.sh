from authlib.integrations.flask_client import OAuth
from flask import Flask, render_template, url_for, session, redirect

import models
from cli import bp as cli_bp

app = Flask(__name__)
app.config.from_pyfile("settings.py")

oauth = OAuth(app)
oauth.register("garmin", fetch_token=lambda: session.get("token"))

models.init_app(app)
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
