"""
Datos del negocio: precios e ingredientes.

Si mañana cambia el menú o los precios, este es el único archivo a tocar;
la lógica de conversación (app/conversation.py) no sabe nada de precios.
"""

from app.models import Drink, PizzaType, Size, Topping

PIZZA_INGREDIENTS: dict[PizzaType, str] = {
    PizzaType.MARGARITA: "tomate, mozzarella y albahaca",
    PizzaType.HAWAIANA: "jamón y piña",
    PizzaType.PEPPERONI: "tomate, mozzarella y pepperoni",
    PizzaType.VEGETARIANA: "tomate, mozzarella, champiñones, pimiento y aceitunas",
    PizzaType.CUATRO_QUESOS: "mozzarella, gorgonzola, parmesano y emmental",
    PizzaType.BARBACOA: "salsa barbacoa, pollo, cebolla y mozzarella",
    PizzaType.CARBONARA: "guanciale, huevo, pimienta y parmesano",
    PizzaType.DIAVOLA: "tomate, mozzarella, salami picante y guindilla",
}

# Precio base de la pizza en tamaño "individual" (EUR).
PIZZA_BASE_PRICE: dict[PizzaType, float] = {
    PizzaType.MARGARITA: 9.50,
    PizzaType.HAWAIANA: 10.50,
    PizzaType.PEPPERONI: 10.50,
    PizzaType.VEGETARIANA: 10.90,
    PizzaType.CUATRO_QUESOS: 11.50,
    PizzaType.BARBACOA: 12.90,
    PizzaType.CARBONARA: 12.90,
    PizzaType.DIAVOLA: 11.50,
}

# El tamaño multiplica el precio base.
SIZE_MULTIPLIER: dict[Size, float] = {
    Size.INDIVIDUAL: 1.0,
    Size.MEDIANA: 1.4,
    Size.FAMILIAR: 2.0,
}

TOPPING_PRICE: dict[Topping, float] = {
    Topping.QUESO_EXTRA: 1.20,
    Topping.BACON: 1.50,
    Topping.CHAMPINONES: 1.00,
    Topping.ACEITUNAS: 0.80,
    Topping.JALAPENOS: 1.00,
    Topping.CEBOLLA: 0.60,
    Topping.PICANTE: 0.50,
}

DRINK_PRICE: dict[Drink, float] = {
    Drink.AGUA: 1.50,
    Drink.COLA: 2.00,
    Drink.NARANJA: 2.00,
    Drink.LIMON: 2.00,
    Drink.CERVEZA: 2.50,
    Drink.ZUMO: 2.20,
}


def pizza_unit_price(pizza: PizzaType, size: Size, extras: list[Topping]) -> float:
    """Precio de UNA pizza (con extras), sin multiplicar por cantidad."""
    base = PIZZA_BASE_PRICE[pizza] * SIZE_MULTIPLIER[size]
    extras_cost = sum(TOPPING_PRICE[t] for t in extras)
    return round(base + extras_cost, 2)


def order_total(pizza: PizzaType, size: Size, quantity: int, extras: list[Topping], drink: Drink | None) -> float:
    total = pizza_unit_price(pizza, size, extras) * quantity
    if drink:
        total += DRINK_PRICE[drink]
    return round(total, 2)