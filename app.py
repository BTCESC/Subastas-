from functools import wraps
from pathlib import Path
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from db import obtener_usuario_por_username


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped_view


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/coleccion")
def coleccion():
    return render_template("coleccion.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario_id"):
        return redirect(url_for("coleccion"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        usuario = obtener_usuario_por_username(username)

        if usuario and usuario["activo"] and check_password_hash(usuario["password_hash"], password):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["username"] = usuario["username"]
            session["nombre_visible"] = usuario["nombre_visible"]

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)

            return redirect(url_for("coleccion"))

        flash("Usuario o contraseña incorrectos.")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/obras/nueva", methods=["GET", "POST"])
@login_required
def nueva_obra():
    form_data = None

    if request.method == "POST":
        form_data = request.form

    return render_template("nueva_obra.html", form_data=form_data)


if __name__ == "__main__":
    app.run(debug=True)
