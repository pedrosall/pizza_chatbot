from app.models import Drink, Order, PizzaType, Size, Topping

PIZZA_INGREDIENTS = {
    PizzaType.MARGARITA: "tomate, mozzarella y albahaca",
    PizzaType.HAWAIANA: "jamón y piña",
    PizzaType.PEPPERONI: "tomate, mozzarella y pepperoni",
    PizzaType.VEGETARIANA: "tomate, mozzarella, champiñones, pimiento y aceitunas",
    PizzaType.CUATRO_QUESOS: "mozzarella, gorgonzola, parmesano y emmental",
    PizzaType.BARBACOA: "salsa barbacoa, pollo, cebolla y mozzarella",
    PizzaType.CARBONARA: "nata, bacon, huevo y parmesano",
    PizzaType.DIAVOLA: "tomate, mozzarella, salami picante y guindilla",
}

PIZZA_BASE_PRICE = {
    PizzaType.MARGARITA: 6.50,
    PizzaType.HAWAIANA: 7.50,
    PizzaType.PEPPERONI: 7.50,
    PizzaType.VEGETARIANA: 7.90,
    PizzaType.CUATRO_QUESOS: 8.50,
    PizzaType.BARBACOA: 8.90,
    PizzaType.CARBONARA: 8.90,
    PizzaType.DIAVOLA: 8.50,
}

SIZE_MULTIPLIER = {
    Size.INDIVIDUAL: 1.0,
    Size.MEDIANA: 1.4,
    Size.FAMILIAR: 2.3,
}

TOPPING_PRICE = {
    Topping.QUESO_EXTRA: 1.20,
    Topping.BACON: 1.50,
    Topping.CHAMPINONES: 1.00,
    Topping.ACEITUNAS: 0.80,
    Topping.JALAPENOS: 1.00,
    Topping.CEBOLLA: 0.60,
    Topping.PICANTE: 0.50,
}

DRINK_PRICE = {
    Drink.AGUA: 1.50,
    Drink.COLA: 2.00,
    Drink.NARANJA: 2.00,
    Drink.CERVEZA: 2.50,
    Drink.ZUMO: 2.20,
}


def pizza_unit_price(pizza, size, extras):
    base = PIZZA_BASE_PRICE[pizza] * SIZE_MULTIPLIER[size]
    extras_cost = sum(TOPPING_PRICE[t] for t in extras)
    return round(base + extras_cost, 2)


def order_total(order: Order) -> float:
    """Suma el carrito completo: todas las pizzas + todas las bebidas."""
    total = 0.0
    for item in order.items:
        total += pizza_unit_price(item.pizza, item.size, item.extras) * item.quantity
    for selection in order.drinks:
        total += DRINK_PRICE[selection.drink] * selection.quantity
    return round(total, 2)