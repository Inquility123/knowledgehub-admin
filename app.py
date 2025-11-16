from flask import Flask, render_template, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from functools import wraps
import requests
import os


app = Flask(__name__)


# ---------------------------------------------------------------------
# Secret key (required for session functionality)
# ---------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise Exception("SECRET_KEY environment variable is missing")

app.secret_key = SECRET_KEY


# ---------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL")

TENANT_ID = os.getenv("AAD_TENANT_ID")
CLIENT_ID = os.getenv("AAD_CLIENT_ID")
CLIENT_SECRET = os.getenv("AAD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("AAD_REDIRECT_URI")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
DISCOVERY_URL = f"{AUTHORITY}/v2.0/.well-known/openid-configuration"


# ---------------------------------------------------------------------
# OAuth Setup
# ---------------------------------------------------------------------
oauth = OAuth(app)
azure = oauth.register(
    name="azure",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url=DISCOVERY_URL,
    client_kwargs={"scope": "openid profile email"},
)


# ---------------------------------------------------------------------
# Login decorator
# ---------------------------------------------------------------------
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("index"))
        return func(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login")
def login():
    return azure.authorize_redirect(redirect_uri=REDIRECT_URI)


@app.route("/auth/callback")
def auth_callback():
    try:
        token = azure.authorize_access_token()
    except Exception as exc:
        return f"OAuth callback error: {exc}", 500

    userinfo = token.get("userinfo") or token.get("id_token_claims")
    if not userinfo:
        return "Login failed: No user info returned", 400

    session["user"] = {
        "name": userinfo.get("name"),
        "email": userinfo.get("preferred_username"),
    }

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    try:
        response = requests.get(f"{BACKEND_URL}/api/measurements/recent?limit=20")
        data = response.json()
    except Exception:
        data = []

    return render_template("dashboard.html",
                           measurements=data,
                           user=session["user"])


# ---------------------------------------------------------------------
# Run (local)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
