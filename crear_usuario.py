from getpass import getpass

from psycopg2 import errors
from werkzeug.security import generate_password_hash

from db import get_connection


def crear_usuario():
    print("Crear usuario privado para la web")
    print("----------------------------------")

    username = input("Usuario: ").strip()
    nombre_visible = input("Nombre visible: ").strip()

    password = getpass("Contraseña: ")
    password_confirm = getpass("Repite la contraseña: ")

    if not username or not nombre_visible or not password:
        print("Error: usuario, nombre visible y contraseña son obligatorios.")
        return

    if password != password_confirm:
        print("Error: las contraseñas no coinciden.")
        return

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO usuarios (username, nombre_visible, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id, username, nombre_visible;
                    """,
                    (username, nombre_visible, password_hash),
                )
                usuario = cur.fetchone()
            conn.commit()

        print("Usuario creado correctamente:")
        print(f"- ID: {usuario['id']}")
        print(f"- Usuario: {usuario['username']}")
        print(f"- Nombre visible: {usuario['nombre_visible']}")

    except errors.UniqueViolation:
        print("Error: ya existe un usuario con ese nombre.")
    except Exception as error:
        print(f"Error inesperado: {error}")


if __name__ == "__main__":
    crear_usuario()
