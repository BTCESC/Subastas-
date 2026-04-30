from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from db import insertar_obra_con_autor, listar_obras, obtener_usuario_por_username


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


def limpiar_texto(valor):
    valor = (valor or "").strip()
    return valor if valor else None


def convertir_decimal_opcional(valor, nombre_campo):
    valor = (valor or "").strip().replace(",", ".")

    if not valor:
        return None

    try:
        return Decimal(valor)
    except InvalidOperation as exc:
        raise ValueError(f"{nombre_campo} debe ser un número válido.") from exc


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/coleccion")
def coleccion():
    obras = listar_obras()
    return render_template("coleccion.html", obras=obras)


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

        autor = limpiar_texto(request.form.get("autor"))
        titulo = limpiar_texto(request.form.get("titulo"))

        if not autor or not titulo:
            flash("Autor y título son obligatorios.")
            return render_template("nueva_obra.html", form_data=form_data)

        try:
            datos_obra = {
                "autor": autor,
                "titulo": titulo,
                "tecnica": limpiar_texto(request.form.get("tecnica")),
                "medidas": limpiar_texto(request.form.get("medidas")),
                "casa_subastas": limpiar_texto(request.form.get("casa_subastas")),
                "fecha_subasta": limpiar_texto(request.form.get("fecha_subasta")),
                "numero_lote": limpiar_texto(request.form.get("numero_lote")),
                "precio_salida": convertir_decimal_opcional(
                    request.form.get("precio_salida"),
                    "Precio de salida",
                ),
                "comision_porcentaje": convertir_decimal_opcional(
                    request.form.get("comision"),
                    "Comisión",
                ),
                "enlace_original": limpiar_texto(request.form.get("enlace_original")),
                "notas": limpiar_texto(request.form.get("notas")),
            }

            insertar_obra_con_autor(datos_obra, creado_por=session.get("usuario_id"))
            flash("Obra guardada correctamente.")
            return redirect(url_for("coleccion"))

        except ValueError as error:
            flash(str(error))
        except Exception:
            flash("No se pudo guardar la obra. Revisa los datos e inténtalo de nuevo.")

    return render_template("nueva_obra.html", form_data=form_data)


if __name__ == "__main__":
    app.run(debug=True)
