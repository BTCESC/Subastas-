from pathlib import Path
import json
import mimetypes
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


PROMPT_ANALISIS_FICHA = """
Analiza esta imagen de una ficha de subasta de arte.

Extrae solo los datos que aparezcan claramente en la ficha.
No inventes datos.

Devuelve únicamente un JSON válido con esta estructura exacta:

{
  "autor": "",
  "titulo": "",
  "tecnica": "",
  "medidas": "",
  "numero_lote": "",
  "precio_salida": "",
  "casa_subastas": "",
  "fecha_subasta": ""
}

Reglas:
- Si no encuentras un dato, deja el valor como cadena vacía.
- Si hay un rango de precio, usa el precio más bajo.
- fecha_subasta debe ir en formato YYYY-MM-DD si aparece clara.
- precio_salida debe ser solo un número, sin símbolo de euro.
- No añadas explicaciones.
- No añadas texto fuera del JSON.
"""


def limpiar_json_respuesta(texto):
    texto = texto.strip()

    texto = re.sub(r"^```json", "", texto, flags=re.IGNORECASE).strip()
    texto = re.sub(r"^```", "", texto).strip()
    texto = re.sub(r"```$", "", texto).strip()

    inicio = texto.find("{")
    fin = texto.rfind("}")

    if inicio != -1 and fin != -1:
        texto = texto[inicio:fin + 1]

    return texto


def analizar_ficha_con_gemini(ruta_imagen):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY en el archivo .env.")

    ruta_imagen = Path(ruta_imagen)

    if not ruta_imagen.exists():
        raise RuntimeError("No se encontró la imagen de la ficha.")

    mime_type, _ = mimetypes.guess_type(ruta_imagen)
    if not mime_type:
        mime_type = "image/jpeg"

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
        contents=[
            types.Part.from_bytes(
                data=ruta_imagen.read_bytes(),
                mime_type=mime_type,
            ),
            PROMPT_ANALISIS_FICHA,
        ],
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        ),
    )

    texto = limpiar_json_respuesta(response.text or "")

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise RuntimeError("Gemini no devolvió un JSON válido.") from error

    return {
        "autor": str(datos.get("autor", "") or "").strip(),
        "titulo": str(datos.get("titulo", "") or "").strip(),
        "tecnica": str(datos.get("tecnica", "") or "").strip(),
        "medidas": str(datos.get("medidas", "") or "").strip(),
        "numero_lote": str(datos.get("numero_lote", "") or "").strip(),
        "precio_salida": str(datos.get("precio_salida", "") or "").strip(),
        "casa_subastas": str(datos.get("casa_subastas", "") or "").strip(),
        "fecha_subasta": str(datos.get("fecha_subasta", "") or "").strip(),
    }
