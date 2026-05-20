import argparse
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from db import get_connection


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "imports" / "obras_rows.csv"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"

EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def limpiar_texto(valor):
    valor = (valor or "").strip()
    return valor if valor else None


def convertir_decimal(valor):
    valor = limpiar_texto(valor)

    if not valor:
        return None

    valor = valor.replace("€", "").replace(".", "").replace(",", ".")

    try:
        return Decimal(valor)
    except InvalidOperation:
        return None


def convertir_fecha(valor):
    valor = limpiar_texto(valor)

    if not valor:
        return None

    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            pass

    return None


def extension_desde_url_o_tipo(url, content_type):
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()

    if suffix in EXTENSIONES_PERMITIDAS:
        return suffix

    if content_type:
        content_type = content_type.lower()

        if "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
        if "png" in content_type:
            return ".png"
        if "webp" in content_type:
            return ".webp"
        if "gif" in content_type:
            return ".gif"

    return ".jpg"


def descargar_imagen(url, prefijo):
    url = limpiar_texto(url)

    if not url:
        return None

    request = Request(
        url,
        headers={"User-Agent": "ArchivoSubastasMigracion/1.0"},
    )

    with urlopen(request, timeout=30) as response:
        contenido = response.read()
        content_type = response.headers.get("Content-Type", "")

    extension = extension_desde_url_o_tipo(url, content_type)
    nombre_archivo = f"{prefijo}_{uuid4().hex}{extension}"
    ruta_destino = UPLOAD_FOLDER / nombre_archivo

    ruta_destino.write_bytes(contenido)

    return nombre_archivo


def obtener_o_crear_autor(cur, nombre_autor):
    cur.execute(
        """
        SELECT id
        FROM autores
        WHERE LOWER(TRIM(nombre_principal)) = LOWER(TRIM(%s))
        LIMIT 1;
        """,
        (nombre_autor,),
    )
    autor = cur.fetchone()

    if autor:
        return autor["id"], False

    cur.execute(
        """
        INSERT INTO autores (nombre_principal)
        VALUES (%s)
        RETURNING id;
        """,
        (nombre_autor,),
    )

    return cur.fetchone()["id"], True


def obra_ya_importada(cur, supabase_id):
    if not supabase_id:
        return False

    cur.execute(
        """
        SELECT id
        FROM obras
        WHERE notas ILIKE %s
        LIMIT 1;
        """,
        (f"%ID Supabase: {supabase_id}%",),
    )

    return cur.fetchone() is not None


def leer_csv():
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as archivo:
        reader = csv.DictReader(archivo)
        return list(reader)


def construir_notas(fila):
    partes = [
        "Migrado desde Supabase.",
        f"ID Supabase: {limpiar_texto(fila.get('id')) or 'sin id'}",
    ]

    ratio = limpiar_texto(fila.get("ratio"))
    if ratio:
        partes.append(f"Ratio original: {ratio}")

    precio_real = limpiar_texto(fila.get("precio_real"))
    if precio_real:
        partes.append(f"Precio real original: {precio_real}")

    imagen_cuadro = limpiar_texto(fila.get("imagen_cuadro"))
    if imagen_cuadro:
        partes.append(f"URL original imagen cuadro: {imagen_cuadro}")

    imagen_ficha = limpiar_texto(fila.get("imagen_ficha"))
    if imagen_ficha:
        partes.append(f"URL original imagen ficha: {imagen_ficha}")

    return "\n".join(partes)


def migrar(ejecutar=False, limite=None):
    filas = leer_csv()

    if limite:
        filas = filas[:limite]

    print(f"Filas encontradas en CSV: {len(filas)}")
    print(f"Modo ejecución real: {'SÍ' if ejecutar else 'NO, solo prueba'}")

    total_con_autor = sum(1 for fila in filas if limpiar_texto(fila.get("autor")))
    total_con_imagen_cuadro = sum(1 for fila in filas if limpiar_texto(fila.get("imagen_cuadro")))
    total_con_imagen_ficha = sum(1 for fila in filas if limpiar_texto(fila.get("imagen_ficha")))

    print(f"Filas con autor: {total_con_autor}")
    print(f"Filas con imagen de cuadro: {total_con_imagen_cuadro}")
    print(f"Filas con imagen de ficha: {total_con_imagen_ficha}")

    if not ejecutar:
        print("\nModo prueba terminado. No se ha insertado nada.")
        print("Para importar de verdad: python3 migrar_supabase_csv.py --execute")
        return

    importadas = 0
    saltadas = 0
    autores_creados = 0
    errores_imagen = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            for fila in filas:
                supabase_id = limpiar_texto(fila.get("id"))

                if obra_ya_importada(cur, supabase_id):
                    saltadas += 1
                    continue

                autor = limpiar_texto(fila.get("autor")) or "Autor desconocido"
                tecnica = limpiar_texto(fila.get("tecnica"))
                casa = limpiar_texto(fila.get("casa"))
                fecha = convertir_fecha(fila.get("fecha"))
                precio_real = convertir_decimal(fila.get("precio_real"))

                autor_id, creado = obtener_o_crear_autor(cur, autor)
                if creado:
                    autores_creados += 1

                imagen_obra = None
                imagen_ficha = None

                try:
                    imagen_obra = descargar_imagen(fila.get("imagen_cuadro"), "obra")
                except Exception as error:
                    errores_imagen += 1
                    print(f"[AVISO] No se pudo descargar imagen de cuadro de {supabase_id}: {error}")

                try:
                    imagen_ficha = descargar_imagen(fila.get("imagen_ficha"), "ficha")
                except Exception as error:
                    errores_imagen += 1
                    print(f"[AVISO] No se pudo descargar imagen de ficha de {supabase_id}: {error}")

                cur.execute(
                    """
                    INSERT INTO obras (
                        autor_id,
                        titulo,
                        tecnica,
                        casa_subastas,
                        fecha_subasta,
                        precio_salida,
                        imagen_obra,
                        imagen_ficha,
                        migracion_info,
                        estado
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'borrador');
                    """,
                    (
                        autor_id,
                        "Sin título",
                        tecnica,
                        casa,
                        fecha,
                        precio_real,
                        imagen_obra,
                        imagen_ficha,
                        construir_notas(fila),
                    ),
                )

                importadas += 1

        conn.commit()

    print("\nMigración completada.")
    print(f"Obras importadas: {importadas}")
    print(f"Obras saltadas por estar ya importadas: {saltadas}")
    print(f"Autores creados: {autores_creados}")
    print(f"Errores de descarga de imagen: {errores_imagen}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Ejecuta la migración real.")
    parser.add_argument("--limit", type=int, help="Limita el número de filas a procesar.")
    args = parser.parse_args()

    migrar(ejecutar=args.execute, limite=args.limit)
