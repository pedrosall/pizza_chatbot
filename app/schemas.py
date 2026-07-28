"""
Esquema de extracción para la IA.

Este modelo es el "contrato" que le imponemos a Gemini: le pedimos que
su respuesta encaje EXACTAMENTE en esta forma (usando structured output),
reutilizando los mismos Enum que ya validan el resto del dominio.

Todos los campos son opcionales porque el cliente puede no haber
mencionado alguno de ellos en su mensaje.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models import PizzaType, Size


class ExtractedOrder(BaseModel):
    pizza: Optional[PizzaType] = None
    size: Optional[Size] = None
    quantity: Optional[int] = Field(default=None, ge=1, le=20)