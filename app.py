from flask import Flask, render_template, redirect, url_for
import requests
import os

app = Flask(__name__)

# URL van jouw ECHTE backend
BACKEND_URL = os.environ.get("BACKEND_URL", "https://kh-backend.azurewebsites.net")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    try:
        response = requests.get(f"{BACKEND_URL}/api/measurements/recent?limit=20")
        measurements = response.json()
    except Exception as e:
        print("BACKEND ERROR:", e)
        measurements = []

    return render_template("dashboard.html", measurements=measurements)


if __name__ == "__main__":
    app.run()
