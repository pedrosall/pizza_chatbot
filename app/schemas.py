"""Esquemas de extracción y validación para la capa de IA."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models import PizzaType, Size


class ExtractedItem(BaseModel):
    pizza: Optional[PizzaType] = None
    size: Optional[Size] = None
    quantity: Optional[int] = Field(default=None, ge=1, le=20)


class ExtractedOrder(BaseModel):
    items: list[ExtractedItem] = Field(default_factory=list)


class ValidationCheck(BaseModel):
    """Resultado de validar un campo de texto libre (dirección, notas)."""

    valid: bool
    reason: Optional[str] = Field(default=None, description="Motivo breve si valid=False")