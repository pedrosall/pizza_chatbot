"""
Máquina de estados de la conversación.

Diseño clave: esta clase NO sabe nada de Telegram. Recibe texto del usuario,
devuelve texto de respuesta. Eso significa que:
  1. Podemos testearla sin levantar un bot.
  2. En la Fase 3, `bot/telegram_bot.py` será una capa fina que solo
     conecta mensajes de Telegram <-> esta clase.
  3. En la Fase 1, sustituiremos los métodos `_extract_*` (basados en
     keywords) por llamadas a Gemini, sin tocar el resto de la máquina.
"""

from __future__ import annotations

from enum import Enum, auto

from pydantic import ValidationError

from app.catalog import PIZZA_INGREDIENTS, order_total
from app.models import Drink, Order, OrderItem, PizzaType, Size, Topping


class ConversationState(Enum):
    ASK_NAME = auto()
    ASK_PIZZA = auto()
    ASK_SIZE = auto()
    ASK_QUANTITY = auto()
    ASK_EXTRAS = auto()
    ASK_DRINK = auto()
    ASK_NOTES = auto()
    ASK_ADDRESS = auto()
    CONFIRM = auto()
    DONE = auto()
    CANCELLED = auto()


class Conversation:
    """Una instancia = una conversación con un cliente concreto."""

    def __init__(self) -> None:
        self.state = ConversationState.ASK_NAME
        self._data: dict = {"extras": []}

    # ---- API pública ---------------------------------------------------

    def handle_message(self, text: str) -> str:
        """Punto de entrada único: texto crudo del usuario -> respuesta."""
        text = text.strip()
        handler = getattr(self, f"_handle_{self.state.name.lower()}")
        return handler(text)

    @property
    def is_finished(self) -> bool:
        return self.state in (ConversationState.DONE, ConversationState.CANCELLED)

    # ---- Handlers por estado -------------------------------------------

    def _handle_ask_name(self, text: str) -> str:
        if not text:
            return "No te he entendido, ¿cómo te llamas?"
        self._data["customer_name"] = text
        self.state = ConversationState.ASK_PIZZA
        opciones = ", ".join(p.value for p in PizzaType)
        return f"Encantado {text.capitalize()} 🍕 ¿Qué pizza te apetece?\nOpciones: {opciones}"

    def _handle_ask_pizza(self, text: str) -> str:
        lowered = text.lower()

        if "lleva" in lowered or "ingredientes" in lowered:
            for pizza, ingredients in PIZZA_INGREDIENTS.items():
                if pizza.value in lowered:
                    return f"La {pizza.value} lleva {ingredients}."
            return "Dime de qué pizza quieres saber los ingredientes."

        pizza = self._extract_pizza(lowered)
        if pizza is None:
            opciones = ", ".join(p.value for p in PizzaType)
            return f"No tenemos esa pizza. Opciones: {opciones}"

        self._data["pizza"] = pizza
        self.state = ConversationState.ASK_SIZE
        return f"Perfecto, una {pizza.value}. ¿Qué tamaño quieres? individual, mediana o familiar"

    def _handle_ask_size(self, text: str) -> str:
        size = self._extract_size(text.lower())
        if size is None:
            return "Elige un tamaño: individual, mediana o familiar"
        self._data["size"] = size
        self.state = ConversationState.ASK_QUANTITY
        return "¿Cuántas unidades?"

    def _handle_ask_quantity(self, text: str) -> str:
        qty = self._extract_quantity(text.lower())
        if qty is None:
            return "Dime un número de unidades (por ejemplo: 2)"
        self._data["quantity"] = qty
        self.state = ConversationState.ASK_EXTRAS
        opciones = ", ".join(t.value for t in Topping)
        return f"¿Algún ingrediente extra? {opciones}\n(separa varios con comas, o escribe 'no')"

    def _handle_ask_extras(self, text: str) -> str:
        lowered = text.lower()
        if lowered != "no":
            extras = self._extract_toppings(lowered)
            if not extras:
                opciones = ", ".join(t.value for t in Topping)
                return f"No he reconocido ningún extra. Opciones: {opciones} (o escribe 'no')"
            self._data["extras"] = extras

        self.state = ConversationState.ASK_DRINK
        opciones = ", ".join(d.value for d in Drink)
        return f"¿Quieres alguna bebida?\nBebidas: {opciones} o escribe 'no'"

    def _handle_ask_drink(self, text: str) -> str:
        lowered = text.lower()
        if lowered == "no":
            self._data["drink"] = None
        else:
            drink = self._extract_drink(lowered)
            if drink is None:
                opciones = ", ".join(d.value for d in Drink)
                return f"Elige una bebida válida ({opciones}) o escribe 'no'"
            self._data["drink"] = drink

        self.state = ConversationState.ASK_NOTES
        return "¿Alguna alergia o petición especial? (o escribe 'no')"

    def _handle_ask_notes(self, text: str) -> str:
        lowered = text.lower()
        self._data["notes"] = None if lowered == "no" else text

        self.state = ConversationState.ASK_ADDRESS
        return "¿Cuál es tu dirección de entrega?"

    def _handle_ask_address(self, text: str) -> str:
        if len(text) < 5:
            return "Esa dirección parece incompleta, ¿puedes darme más detalle?"
        self._data["address"] = text

        order, error = self._build_order()
        if error:
            self.state = ConversationState.CANCELLED
            return f"Algo no cuadra en el pedido ({error}). Escribe /start para empezar de nuevo."

        self._data["order"] = order
        self.state = ConversationState.CONFIRM
        total = order_total(
            order.item.pizza, order.item.size, order.item.quantity, order.item.extras, order.drink
        )
        return f"{order.summary()}\n💶 Total: {total}€\n\n¿Confirmamos? (sí/no)"

    def _handle_confirm(self, text: str) -> str:
        lowered = text.lower()
        if lowered in ("si", "sí"):
            self.state = ConversationState.DONE
            return "🍕 Pedido confirmado. ¡En camino!"
        self.state = ConversationState.CANCELLED
        return "Pedido cancelado. Escribe /start si quieres hacer otro."

    # ---- Extracción (Fase 0: keywords · Fase 1: aquí entrará Gemini) --

    @staticmethod
    def _extract_pizza(lowered: str) -> PizzaType | None:
        for pizza in PizzaType:
            if pizza.value in lowered:
                return pizza
        return None

    @staticmethod
    def _extract_size(lowered: str) -> Size | None:
        for size in Size:
            if size.value in lowered:
                return size
        return None

    @staticmethod
    def _extract_quantity(lowered: str) -> int | None:
        words_to_numbers = {"una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4}
        if lowered in words_to_numbers:
            return words_to_numbers[lowered]
        if lowered.isdigit():
            qty = int(lowered)
            return qty if 0 < qty <= 20 else None
        return None

    @staticmethod
    def _extract_toppings(lowered: str) -> list[Topping]:
        found = [t for t in Topping if t.value in lowered]
        return list(dict.fromkeys(found))

    @staticmethod
    def _extract_drink(lowered: str) -> Drink | None:
        for drink in Drink:
            if drink.value in lowered:
                return drink
        return None

    def _build_order(self) -> tuple[Order | None, str | None]:
        try:
            item = OrderItem(
                pizza=self._data["pizza"],
                size=self._data["size"],
                quantity=self._data["quantity"],
                extras=self._data.get("extras", []),
            )
            order = Order(
                customer_name=self._data["customer_name"],
                item=item,
                drink=self._data.get("drink"),
                address=self._data["address"],
                notes=self._data.get("notes"),
            )
            return order, None
        except ValidationError as exc:
            return None, str(exc)