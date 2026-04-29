from flask import Flask, render_template, request
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/coleccion")
def coleccion():
    return render_template("coleccion.html")


@app.route("/obras/nueva", methods=["GET", "POST"])
def nueva_obra():
    form_data = None

    if request.method == "POST":
        form_data = request.form

    return render_template("nueva_obra.html", form_data=form_data)


if __name__ == "__main__":
    app.run(debug=True)
