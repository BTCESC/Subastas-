from pathlib import Path
import os

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        cursor_factory=RealDictCursor,
    )


def init_db():
    schema_path = BASE_DIR / "schema.sql"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_path.read_text(encoding="utf-8"))
        conn.commit()


def listar_tablas():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            return [row["table_name"] for row in cur.fetchall()]


def obtener_usuario_por_username(username):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, nombre_visible, password_hash, activo
                FROM usuarios
                WHERE username = %s
                LIMIT 1;
                """,
                (username,),
            )
            return cur.fetchone()


def insertar_obra_con_autor(datos_obra, creado_por=None):
    nombre_autor = datos_obra["autor"].strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
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
                autor_id = autor["id"]
            else:
                cur.execute(
                    """
                    INSERT INTO autores (nombre_principal)
                    VALUES (%s)
                    RETURNING id;
                    """,
                    (nombre_autor,),
                )
                autor_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO obras (
                    autor_id,
                    creado_por,
                    titulo,
                    tecnica,
                    medidas,
                    casa_subastas,
                    fecha_subasta,
                    numero_lote,
                    precio_salida,
                    comision_porcentaje,
                    enlace_original,
                    notas
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    autor_id,
                    creado_por,
                    datos_obra["titulo"],
                    datos_obra.get("tecnica"),
                    datos_obra.get("medidas"),
                    datos_obra.get("casa_subastas"),
                    datos_obra.get("fecha_subasta"),
                    datos_obra.get("numero_lote"),
                    datos_obra.get("precio_salida"),
                    datos_obra.get("comision_porcentaje"),
                    datos_obra.get("enlace_original"),
                    datos_obra.get("notas"),
                ),
            )

            obra_id = cur.fetchone()["id"]

        conn.commit()

    return obra_id


def listar_obras():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    obras.id,
                    obras.titulo,
                    obras.tecnica,
                    obras.medidas,
                    obras.casa_subastas,
                    obras.fecha_subasta,
                    obras.numero_lote,
                    obras.precio_salida,
                    obras.comision_porcentaje,
                    obras.precio_final,
                    obras.creado_en,
                    autores.nombre_principal AS autor
                FROM obras
                JOIN autores ON autores.id = obras.autor_id
                ORDER BY obras.creado_en DESC;
                """
            )
            return cur.fetchall()


if __name__ == "__main__":
    init_db()
    tablas = listar_tablas()

    print("Esquema aplicado correctamente.")
    print("Tablas encontradas:")
    for tabla in tablas:
        print(f"- {tabla}")
