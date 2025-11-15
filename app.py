from flask import Flask, render_template, redirect, url_for
import requests
import os

app = Flask(__name__)

# Backend API URL (Azure backend)
BACKEND_URL = os.environ.get("BACKEND_URL", "https://kh-api-app.azurewebsites.net")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    try:
        # Call backend API
        r = requests.get(f"{BACKEND_URL}/api/measurements/recent?limit=20")
        data = r.json()
    except Exception as e:
        data = []
        print("API ERROR:", e)

    return render_template("dashboard.html", measurements=data)


if __name__ == "__main__":
    app.run(debug=True)
