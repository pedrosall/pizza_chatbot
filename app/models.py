"""
Modelos de dominio del pedido.

Por qué Pydantic y no dicts sueltos:
- Validación automática (si `size` no es válido, falla aquí, no 3 pasos después).
- Autocompletado y tipado en el editor.
- Estos mismos modelos se reutilizarán en la Fase 1 para forzar a Gemini
  a devolver datos con una forma exacta (structured output).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PizzaType(str, Enum):
    MARGARITA = "margarita"
    HAWAIANA = "hawaiana"
    PEPPERONI = "pepperoni"
    VEGETARIANA = "vegetariana"
    CUATRO_QUESOS = "cuatro quesos"
    BARBACOA = "barbacoa"
    CARBONARA = "carbonara"
    DIAVOLA = "diavola"


class Size(str, Enum):
    INDIVIDUAL = "individual"
    MEDIANA = "mediana"
    FAMILIAR = "familiar"


class Drink(str, Enum):
    AGUA = "agua"
    COLA = "cola"
    NARANJA = "naranja"
    LIMON = "limón"
    CERVEZA = "cerveza"
    ZUMO = "zumo"


class Topping(str, Enum):
    """Ingrediente extra que se puede añadir a una pizza, con coste aparte."""

    QUESO_EXTRA = "queso extra"
    BACON = "bacon"
    CHAMPINONES = "champiñones"
    ACEITUNAS = "aceitunas"
    JALAPENOS = "jalapeños"
    CEBOLLA = "cebolla"
    PICANTE = "picante"


class OrderItem(BaseModel):
    """Una pizza dentro del pedido (más adelante permitiremos varias en un mismo pedido)."""

    pizza: PizzaType
    size: Size
    quantity: int = Field(gt=0, le=20)
    extras: list[Topping] = Field(default_factory=list)

    @field_validator("extras")
    @classmethod
    def _no_duplicate_extras(cls, v: list[Topping]) -> list[Topping]:
        # Pedir "bacon" dos veces no debería duplicar el cargo.
        return list(dict.fromkeys(v))


class Order(BaseModel):
    """El pedido completo de un cliente."""

    customer_name: str = Field(min_length=1, max_length=80)
    item: OrderItem
    drink: Optional[Drink] = None
    address: str = Field(min_length=5, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=200)

    @field_validator("customer_name")
    @classmethod
    def _capitalize_name(cls, v: str) -> str:
        return v.strip().capitalize()

    def summary(self) -> str:
        """Texto de confirmación legible para el cliente."""
        drink_txt = self.drink.value if self.drink else "sin bebida"
        extras_txt = f" + {', '.join(e.value for e in self.item.extras)}" if self.item.extras else ""
        notes_txt = f"\n📝 {self.notes}" if self.notes else ""
        return (
            f"👤 {self.customer_name}\n"
            f"🍕 {self.item.quantity}x {self.item.pizza.value} ({self.item.size.value}){extras_txt}\n"
            f"🥤 {drink_txt}"
            f"{notes_txt}\n"
            f"📍 {self.address}"
        )