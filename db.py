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
        return autor["id"]

    cur.execute(
        """
        INSERT INTO autores (nombre_principal)
        VALUES (%s)
        RETURNING id;
        """,
        (nombre_autor,),
    )
    return cur.fetchone()["id"]


def insertar_obra_con_autor(datos_obra, creado_por=None):
    nombre_autor = datos_obra["autor"].strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            autor_id = obtener_o_crear_autor(cur, nombre_autor)

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
                    imagen_obra,
                    imagen_ficha,
                    notas,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    datos_obra.get("imagen_obra"),
                    datos_obra.get("imagen_ficha"),
                    datos_obra.get("notas"),
                    datos_obra.get("estado", "publicada"),
                ),
            )

            obra_id = cur.fetchone()["id"]

        conn.commit()

    return obra_id


def listar_obras(busqueda=None, estado=None):
    busqueda = (busqueda or "").strip()
    estado = (estado or "").strip()

    if estado not in {"publicada", "borrador"}:
        estado = None

    with get_connection() as conn:
        with conn.cursor() as cur:
            condiciones = []
            parametros = []

            if busqueda:
                condiciones.append("""
                    (
                        obras.titulo ILIKE %s
                        OR autores.nombre_principal ILIKE %s
                        OR obras.casa_subastas ILIKE %s
                    )
                """)
                patron = f"%{busqueda}%"
                parametros.extend([patron, patron, patron])

            if estado:
                condiciones.append("obras.estado = %s")
                parametros.append(estado)

            where_sql = ""
            if condiciones:
                where_sql = "WHERE " + " AND ".join(condiciones)

            cur.execute(
                f"""
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
                    obras.imagen_obra,
                    obras.imagen_ficha,
                    obras.estado,
                    obras.creado_en,
                    autores.nombre_principal AS autor
                FROM obras
                JOIN autores ON autores.id = obras.autor_id
                {where_sql}
                ORDER BY obras.creado_en DESC;
                """,
                parametros,
            )
            return cur.fetchall()


def obtener_obra_por_id(obra_id):
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
                    obras.enlace_original,
                    obras.imagen_obra,
                    obras.imagen_ficha,
                    obras.notas,
                    obras.estado,
                    autores.nombre_principal AS autor
                FROM obras
                JOIN autores ON autores.id = obras.autor_id
                WHERE obras.id = %s
                LIMIT 1;
                """,
                (obra_id,),
            )
            return cur.fetchone()


def actualizar_obra(obra_id, datos_obra):
    nombre_autor = datos_obra["autor"].strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            autor_id = obtener_o_crear_autor(cur, nombre_autor)

            cur.execute(
                """
                UPDATE obras
                SET
                    autor_id = %s,
                    titulo = %s,
                    tecnica = %s,
                    medidas = %s,
                    casa_subastas = %s,
                    fecha_subasta = %s,
                    numero_lote = %s,
                    precio_salida = %s,
                    comision_porcentaje = %s,
                    enlace_original = %s,
                    imagen_obra = %s,
                    imagen_ficha = %s,
                    notas = %s,
                    estado = %s,
                    actualizado_en = NOW()
                WHERE id = %s
                RETURNING id;
                """,
                (
                    autor_id,
                    datos_obra["titulo"],
                    datos_obra.get("tecnica"),
                    datos_obra.get("medidas"),
                    datos_obra.get("casa_subastas"),
                    datos_obra.get("fecha_subasta"),
                    datos_obra.get("numero_lote"),
                    datos_obra.get("precio_salida"),
                    datos_obra.get("comision_porcentaje"),
                    datos_obra.get("enlace_original"),
                    datos_obra.get("imagen_obra"),
                    datos_obra.get("imagen_ficha"),
                    datos_obra.get("notas"),
                    datos_obra.get("estado", "publicada"),
                    obra_id,
                ),
            )

            obra_actualizada = cur.fetchone()

        conn.commit()

    return obra_actualizada is not None


def borrar_obra(obra_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM obras
                WHERE id = %s
                RETURNING id, imagen_obra, imagen_ficha;
                """,
                (obra_id,),
            )
            obra_borrada = cur.fetchone()

        conn.commit()

    return obra_borrada

def listar_autores():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    autores.id,
                    autores.nombre_principal,
                    autores.notas,
                    autores.creado_en,
                    COUNT(obras.id) AS total_obras
                FROM autores
                LEFT JOIN obras ON obras.autor_id = autores.id
                GROUP BY autores.id
                ORDER BY LOWER(autores.nombre_principal);
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
