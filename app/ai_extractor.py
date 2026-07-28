"""
Capa de extracción con IA.

Principio de diseño: esta función NUNCA debe reventar el flujo del bot.
Si Gemini falla (sin API key, sin red, respuesta inesperada), devuelve
None y quien la llame debe caer de vuelta a las reglas por keywords.
La IA es una mejora, no una dependencia crítica.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schemas import ExtractedOrder

load_dotenv()
logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client | None:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY no configurada; extracción con IA desactivada.")
            return None
        _client = genai.Client(api_key=api_key)
    return _client


_PROMPT = """Eres un extractor de datos para el pedido de una pizzería.
Analiza el mensaje del cliente y extrae ÚNICAMENTE los datos que se mencionen
de forma explícita: qué pizza, qué tamaño y cuántas unidades.

Reglas estrictas:
- No inventes ni asumas datos que no estén en el mensaje.
- Si un dato no aparece, déjalo vacío (null).
- No confundas ingredientes o extras con el tipo de pizza.

Mensaje del cliente: "{text}"
"""


def extract_order_info(text: str) -> ExtractedOrder | None:
    """Intenta extraer pizza/tamaño/cantidad de un mensaje libre. None si falla."""
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=_PROMPT.format(text=text),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedOrder,
            ),
        )
        return response.parsed
    except Exception as exc:  # noqa: BLE001 — cualquier fallo cae a las reglas
        logger.warning("Fallo en extracción con Gemini: %s", exc)
        return None