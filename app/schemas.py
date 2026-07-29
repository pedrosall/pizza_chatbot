"""Esquema de extracción para la IA — ahora una LISTA de pizzas por mensaje."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models import PizzaType, Size


class ExtractedItem(BaseModel):
    pizza: Optional[PizzaType] = None
    size: Optional[Size] = None
    quantity: Optional[int] = Field(default=None, ge=1, le=20)


class ExtractedOrder(BaseModel):
    """Un mensaje puede mencionar varias pizzas distintas a la vez."""

    items: list[ExtractedItem] = Field(default_factory=list)