from flask import Flask, render_template, redirect, url_for, session, request
from authlib.integrations.flask_client import OAuth
from functools import wraps
import requests
import os

app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.getenv("SECRET_KEY", "dev")

# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL")

# Azure AD config
TENANT_ID = os.getenv("AAD_TENANT_ID")
CLIENT_ID = os.getenv("AAD_CLIENT_ID")
CLIENT_SECRET = os.getenv("AAD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("AAD_REDIRECT_URI")

# Azure AD endpoints
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
DISCOVERY_URL = f"{AUTHORITY}/v2.0/.well-known/openid-configuration"

# OAuth setup
oauth = OAuth(app)
azure = oauth.register(
    name="azure",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url=DISCOVERY_URL,
    client_kwargs={
        "scope": "openid profile email https://graph.microsoft.com/.default"
    },
)


# Login required decorator
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


# -----------------------
# ROUTES
# -----------------------

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
    # Tokens ophalen
    token = azure.authorize_access_token()

    # Userinfo via Microsoft Graph OIDC
    resp = oauth.azure.get(
        "https://graph.microsoft.com/oidc/userinfo",
        token=token
    )
    userinfo = resp.json()

    # User opslaan in session
    session["user"] = {
        "name": userinfo.get("name"),
        "email": userinfo.get("email") or userinfo.get("preferred_username")
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
    except Exception as e:
        print("Backend error:", e)
        data = []

    return render_template(
        "dashboard.html",
        measurements=data,
        user=session["user"]
    )


# -----------------------
# APP RUN
# -----------------------

if __name__ == "__main__":
    app.run(debug=True)
