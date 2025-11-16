from flask import Flask, render_template, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from functools import wraps
import requests
import os

app = Flask(__name__)

# Secret key for signing session cookies
app.secret_key = os.environ.get("SECRET_KEY", "development")

# Backend API URL
BACKEND_URL = os.environ.get("BACKEND_URL", "https://kh-api-app.azurewebsites.net")

# Azure AD config
TENANT_ID = os.environ.get("AAD_TENANT_ID")
CLIENT_ID = os.environ.get("AAD_CLIENT_ID")
CLIENT_SECRET = os.environ.get("AAD_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("AAD_REDIRECT_URI")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
DISCOVERY_URL = f"{AUTHORITY}/v2.0/.well-known/openid-configuration"

oauth = OAuth(app)
azure = oauth.register(
    name="azure",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url=DISCOVERY_URL,
    client_kwargs={"scope": "openid profile email"},
)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login")
def login():
    return azure.authorize_redirect(REDIRECT_URI)


@app.route("/auth/callback")
def auth_callback():
    token = azure.authorize_access_token()
    userinfo = token.get("userinfo") or token.get("id_token_claims")

    if not userinfo:
        return "Login failed: no user info", 400

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
        r = requests.get(f"{BACKEND_URL}/api/measurements/recent?limit=20")
        data = r.json()
    except:
        data = []

    return render_template("dashboard.html", measurements=data, user=session["user"])


if __name__ == "__main__":
    app.run(debug=True)
