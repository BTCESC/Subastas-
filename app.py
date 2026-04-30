from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path
from uuid import uuid4
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from ai import analizar_ficha_con_gemini
from db import (
    actualizar_obra,
    borrar_obra,
    insertar_obra_con_autor,
    listar_autores,
    listar_obras,
    obtener_obra_por_id,
    obtener_usuario_por_username,
)


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

EXTENSIONES_IMAGEN_PERMITIDAS = {"jpg", "jpeg", "png", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


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


def extension_permitida(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_IMAGEN_PERMITIDAS


def guardar_imagen_subida(archivo, prefijo):
    if not archivo or not archivo.filename:
        return None

    nombre_original = secure_filename(archivo.filename)

    if not extension_permitida(nombre_original):
        raise ValueError("Solo se permiten imágenes JPG, JPEG, PNG, WEBP o GIF.")

    extension = nombre_original.rsplit(".", 1)[1].lower()
    nombre_final = f"{prefijo}_{uuid4().hex}.{extension}"
    ruta_destino = UPLOAD_FOLDER / nombre_final

    archivo.save(ruta_destino)

    return nombre_final


def borrar_archivo_subido(nombre_archivo):
    if not nombre_archivo:
        return

    ruta_archivo = (UPLOAD_FOLDER / nombre_archivo).resolve()
    carpeta_uploads = UPLOAD_FOLDER.resolve()

    if carpeta_uploads not in ruta_archivo.parents:
        return

    if ruta_archivo.exists() and ruta_archivo.is_file():
        ruta_archivo.unlink()


def obtener_datos_obra_desde_formulario():
    estado = request.form.get("estado", "publicada")
    if estado not in {"borrador", "publicada"}:
        estado = "publicada"

    return {
        "autor": limpiar_texto(request.form.get("autor")),
        "titulo": limpiar_texto(request.form.get("titulo")),
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
        "estado": estado,
    }


def preparar_form_data_desde_obra(obra):
    return {
        "autor": obra["autor"],
        "titulo": obra["titulo"],
        "tecnica": obra["tecnica"] or "",
        "medidas": obra["medidas"] or "",
        "casa_subastas": obra["casa_subastas"] or "",
        "fecha_subasta": obra["fecha_subasta"].isoformat() if obra["fecha_subasta"] else "",
        "numero_lote": obra["numero_lote"] or "",
        "precio_salida": obra["precio_salida"] or "",
        "comision": obra["comision_porcentaje"] or "",
        "enlace_original": obra["enlace_original"] or "",
        "notas": obra["notas"] or "",
        "estado": obra["estado"] or "publicada",
        "imagen_obra_existente": obra["imagen_obra"] or "",
        "imagen_ficha_existente": obra["imagen_ficha"] or "",
    }


def mezclar_datos_ia_con_formulario(formulario, datos_ia, imagen_obra=None, imagen_ficha=None):
    form_data = dict(formulario)

    campos = [
        "autor",
        "titulo",
        "tecnica",
        "medidas",
        "numero_lote",
        "precio_salida",
        "casa_subastas",
        "fecha_subasta",
    ]

    for campo in campos:
        valor_actual = (form_data.get(campo) or "").strip()
        valor_ia = (datos_ia.get(campo) or "").strip()

        if not valor_actual and valor_ia:
            form_data[campo] = valor_ia

    if imagen_obra:
        form_data["imagen_obra_existente"] = imagen_obra

    if imagen_ficha:
        form_data["imagen_ficha_existente"] = imagen_ficha

    return form_data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/panel")
@login_required
def panel():
    return render_template("panel.html")


@app.route("/autores")
@login_required
def autores():
    autores = listar_autores()
    return render_template("autores.html", autores=autores)


@app.route("/coleccion")
def coleccion():
    busqueda = request.args.get("q", "").strip()
    estado_filtro = request.args.get("estado", "").strip()

    if estado_filtro not in {"publicada", "borrador"}:
        estado_filtro = ""

    obras = listar_obras(busqueda, estado_filtro)
    return render_template(
        "coleccion.html",
        obras=obras,
        q=busqueda,
        estado_filtro=estado_filtro,
    )


@app.route("/obras/<int:obra_id>")
def detalle_obra(obra_id):
    obra = obtener_obra_por_id(obra_id)

    if not obra:
        flash("No se encontró la obra solicitada.")
        return redirect(url_for("coleccion"))

    return render_template("obra_detalle.html", obra=obra)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario_id"):
        return redirect(url_for("panel"))

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

            return redirect(url_for("panel"))

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
        accion = request.form.get("accion", "guardar")

        try:
            if accion == "analizar_ia":
                imagen_obra_existente = limpiar_texto(request.form.get("imagen_obra_existente"))
                imagen_ficha_existente = limpiar_texto(request.form.get("imagen_ficha_existente"))

                nueva_imagen_obra = guardar_imagen_subida(request.files.get("imagen_obra"), "obra")
                nueva_imagen_ficha = guardar_imagen_subida(request.files.get("imagen_ficha"), "ficha")

                imagen_obra = nueva_imagen_obra or imagen_obra_existente
                imagen_ficha = nueva_imagen_ficha or imagen_ficha_existente

                if not imagen_ficha:
                    flash("Sube una imagen de la ficha antes de usar la IA.")
                    return render_template("nueva_obra.html", form_data=form_data)

                datos_ia = analizar_ficha_con_gemini(UPLOAD_FOLDER / imagen_ficha)
                form_data = mezclar_datos_ia_con_formulario(
                    request.form,
                    datos_ia,
                    imagen_obra=imagen_obra,
                    imagen_ficha=imagen_ficha,
                )

                flash("Ficha analizada con IA. Revisa los datos antes de guardar.")
                return render_template("nueva_obra.html", form_data=form_data)

            datos_obra = obtener_datos_obra_desde_formulario()

            if not datos_obra["autor"] or not datos_obra["titulo"]:
                flash("Autor y título son obligatorios, incluso si la obra queda como borrador.")
                return render_template("nueva_obra.html", form_data=form_data)

            imagen_obra_existente = limpiar_texto(request.form.get("imagen_obra_existente"))
            imagen_ficha_existente = limpiar_texto(request.form.get("imagen_ficha_existente"))

            datos_obra["imagen_obra"] = guardar_imagen_subida(request.files.get("imagen_obra"), "obra") or imagen_obra_existente
            datos_obra["imagen_ficha"] = guardar_imagen_subida(request.files.get("imagen_ficha"), "ficha") or imagen_ficha_existente

            insertar_obra_con_autor(datos_obra, creado_por=session.get("usuario_id"))
            flash("Obra guardada correctamente.")
            return redirect(url_for("coleccion"))

        except ValueError as error:
            flash(str(error))
        except Exception as error:
            error_texto = str(error)

            if "RESOURCE_EXHAUSTED" in error_texto or "429" in error_texto:
                flash("La IA está temporalmente limitada. Espera un minuto y vuelve a intentarlo.")
            elif "API key" in error_texto or "GEMINI_API_KEY" in error_texto:
                flash("No se ha podido usar la IA porque falta o no es válida la clave de Gemini.")
            else:
                flash("No se pudo procesar la ficha con IA. Revisa la imagen e inténtalo de nuevo.")

    return render_template("nueva_obra.html", form_data=form_data)


@app.route("/obras/<int:obra_id>/editar", methods=["GET", "POST"])
@login_required
def editar_obra(obra_id):
    obra = obtener_obra_por_id(obra_id)

    if not obra:
        flash("No se encontró la obra solicitada.")
        return redirect(url_for("coleccion"))

    form_data = preparar_form_data_desde_obra(obra)

    if request.method == "POST":
        form_data = request.form

        try:
            datos_obra = obtener_datos_obra_desde_formulario()

            if not datos_obra["autor"] or not datos_obra["titulo"]:
                flash("Autor y título son obligatorios, incluso si la obra queda como borrador.")
                return render_template("editar_obra.html", obra=obra, form_data=form_data)

            nueva_imagen_obra = guardar_imagen_subida(request.files.get("imagen_obra"), "obra")
            nueva_imagen_ficha = guardar_imagen_subida(request.files.get("imagen_ficha"), "ficha")

            datos_obra["imagen_obra"] = nueva_imagen_obra or obra["imagen_obra"]
            datos_obra["imagen_ficha"] = nueva_imagen_ficha or obra["imagen_ficha"]

            actualizada = actualizar_obra(obra_id, datos_obra)

            if actualizada:
                flash("Obra actualizada correctamente.")
                return redirect(url_for("coleccion"))

            flash("No se encontró la obra solicitada.")

        except ValueError as error:
            flash(str(error))
        except Exception:
            flash("No se pudo actualizar la obra. Revisa los datos e inténtalo de nuevo.")

    return render_template("editar_obra.html", obra=obra, form_data=form_data)


@app.route("/obras/<int:obra_id>/borrar", methods=["POST"])
@login_required
def borrar_obra_route(obra_id):
    obra_borrada = borrar_obra(obra_id)

    if obra_borrada:
        borrar_archivo_subido(obra_borrada.get("imagen_obra"))
        borrar_archivo_subido(obra_borrada.get("imagen_ficha"))
        flash("Obra borrada correctamente.")
    else:
        flash("No se encontró la obra solicitada.")

    return redirect(url_for("coleccion"))


if __name__ == "__main__":
    app.run(debug=True)
