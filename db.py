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


if __name__ == "__main__":
    init_db()
    tablas = listar_tablas()

    print("Esquema aplicado correctamente.")
    print("Tablas encontradas:")
    for tabla in tablas:
        print(f"- {tabla}")
