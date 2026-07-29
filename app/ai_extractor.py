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
Analiza el mensaje del cliente y extrae TODAS las pizzas distintas que
mencione, cada una como un elemento de una lista, con su tamaño y
cantidad SI se mencionan explícitamente.

Reglas estrictas:
- Un mensaje puede mencionar varias pizzas distintas a la vez
  (ej: "una pepperoni y una vegetariana familiar" son DOS elementos).
- No inventes ni asumas datos que no estén en el mensaje.
- Si un dato no aparece para una pizza concreta, déjalo vacío (null).
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

    from app.business_info import BUSINESS_FACTS

_FAQ_PROMPT = """Eres el asistente de atención al cliente de PizzaBot Pizzería, en Telegram.

Datos reales del negocio (SOLO puedes usar esta información, nunca te
inventes horarios, precios o datos que no estén aquí):
{facts}

El cliente ha escrito esto, que NO es directamente un pedido de pizza:
"{text}"

Instrucciones:
- Responde en máximo 3 frases, con tono cercano y un toque de humor si
  el mensaje se presta a ello (bromas, saludos informales, chistes).
- Si preguntan algo ajeno a la pizzería (el tiempo, un chiste, curiosidades),
  contesta brevemente sin problema, con naturalidad.
- Si preguntan algo específico del negocio que no está en los datos de
  arriba, dilo con honestidad en vez de inventarlo.
- Termina SIEMPRE invitando a pedir, con frases variadas, no la misma cada vez.
"""


def answer_off_topic(text: str) -> str | None:
    """Responde a mensajes que no son un pedido (dudas, bromas, charla).

    Igual que extract_order_info: si falla por lo que sea, devuelve None
    y quien la llame debe caer a un mensaje genérico de reserva.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=_FAQ_PROMPT.format(facts=BUSINESS_FACTS, text=text),
        )
        return response.text.strip() if response.text else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fallo en respuesta FAQ con Gemini: %s", exc)
        return None