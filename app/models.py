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
    CERVEZA = "cerveza"
    SPRITE = "sprite"
    LIMONADA = "limonada"


DRINK_DISPLAY_NAMES: dict[Drink, str] = {
    Drink.AGUA: "agua",
    Drink.COLA: "cola",
    Drink.NARANJA: "refresco de naranja",
    Drink.CERVEZA: "cerveza",
    Drink.SPRITE: "sprite",
    Drink.LIMONADA: "limonada",
}


class Topping(str, Enum):
    QUESO_EXTRA = "queso extra"
    BACON = "bacon"
    CHAMPINONES = "champiñones"
    ACEITUNAS = "aceitunas"
    JALAPENOS = "jalapeños"
    CEBOLLA = "cebolla"
    PICANTE = "picante"


class CartItem(BaseModel):
    """Una pizza dentro del carrito. Un pedido puede tener varias."""

    pizza: PizzaType
    size: Size
    quantity: int = Field(gt=0, le=20)
    extras: list[Topping] = Field(default_factory=list)

    @field_validator("extras")
    @classmethod
    def _no_duplicate_extras(cls, v: list[Topping]) -> list[Topping]:
        return list(dict.fromkeys(v))


class DrinkSelection(BaseModel):
    """Una bebida y cuántas unidades. Un pedido puede tener varias distintas."""

    drink: Drink
    quantity: int = Field(gt=0, le=20)


class Order(BaseModel):
    """El pedido completo: un carrito de pizzas + una lista de bebidas."""

    customer_name: str = Field(min_length=1, max_length=80)
    items: list[CartItem] = Field(min_length=1)
    drinks: list[DrinkSelection] = Field(default_factory=list)
    address: str = Field(min_length=5, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=200)

    @field_validator("customer_name")
    @classmethod
    def _capitalize_name(cls, v: str) -> str:
        return v.strip().capitalize()

    def summary(self) -> str:
        lines = [f"👤 {self.customer_name}"]
        for item in self.items:
            extras_txt = (
                f" + {', '.join(e.value for e in item.extras)}" if item.extras else ""
            )
            lines.append(f"🍕 {item.quantity}x {item.pizza.value} ({item.size.value}){extras_txt}")

        if self.drinks:
            drinks_txt = ", ".join(f"{d.quantity}x {DRINK_DISPLAY_NAMES[d.drink]}" for d in self.drinks)
            lines.append(f"🥤 {drinks_txt}")
        else:
            lines.append("🥤 sin bebida")

        if self.notes:
            lines.append(f"📝 {self.notes}")
        lines.append(f"📍 {self.address}")
        return "\n".join(lines)