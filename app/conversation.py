"""
Máquina de estados de la conversación.

Diseño: se toma el pedido completo primero (pueden mencionarse varias
pizzas de golpe, incluso la misma pizza en tamaños distintos), luego
bebidas y notas, y los datos de entrega (nombre, dirección) se piden al
FINAL, como en un pedido real de pizzería por teléfono. Antes de
confirmar, se "repite" el pedido completo para que el cliente pueda
corregir cualquier error.

Cuando un mensaje en ASK_ORDER no contiene ninguna pizza reconocible,
comprobamos primero si es una pregunta sobre el menú (regla simple y
gratuita) y, si no, delegamos en la IA para responder con criterio
(bromas, horarios, dudas genéricas) usando solo datos reales del negocio.
"""

from __future__ import annotations

import re
from enum import Enum, auto

from pydantic import ValidationError

from app.ai_extractor import answer_off_topic, extract_order_info
from app.catalog import PIZZA_INGREDIENTS, order_total
from app.models import CartItem, Drink, DrinkSelection, DRINK_DISPLAY_NAMES, Order, PizzaType, Size, Topping

_BACK_COMMANDS = ("atrás", "atras", "volver")
_WORD_NUMBERS = {"un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5}
_MENU_KEYWORDS = (
    "qué pizzas", "que pizzas", "cuáles tenéis", "cuales teneis",
    "qué tenéis", "que teneis", "menú", "menu", "qué hay", "que hay",
    "opciones", "carta",
)
_SIZE_SYNONYMS = {
    "grande": "familiar",
    "grandes": "familiar",
    "pequeña": "individual",
    "pequeñas": "individual",
    "pequeno": "individual",
    "pequeño": "individual",
    "personal": "individual",
    "chica": "individual",
    "chicas": "individual",
}

_DRINK_SYNONYMS = {
    "cocacola": "cola",
    "coca-cola": "cola",
    "coca cola": "cola",
    "refresco de cola": "cola",
    "limón": "limonada",
    "fanta de limón" : "limonada",
    "limon": "limonada",
    "naranjada": "refresco de naranja",
    "fanta de naranja": "refresco de naranja",
    "sprite": "sprite",
    "7up": "sprite"
}
_DRINK_SPLIT_RE = re.compile(r",| y | e ")


class ConversationState(Enum):
    ASK_ORDER = auto()
    ASK_ITEM_QUANTITY = auto()
    ASK_ITEM_SIZE = auto()
    ASK_ITEM_EXTRAS = auto()
    ASK_MORE_PIZZA = auto()
    ASK_DRINKS = auto()
    ASK_NOTES = auto()
    ASK_NAME = auto()
    ASK_ADDRESS = auto()
    CONFIRM = auto()
    DONE = auto()
    CANCELLED = auto()


class Conversation:
    def __init__(self) -> None:
        self.state = ConversationState.ASK_ORDER
        self._data: dict = {}
        self._pending: list[dict] = []
        self._items: list[CartItem] = []
        self._drinks: list[DrinkSelection] = []
        self._history: list[tuple[ConversationState, str]] = []
        self._last_prompt = ""

    # ---- API pública ---------------------------------------------------

    def greeting(self) -> str:
        self.state = ConversationState.ASK_ORDER
        self._last_prompt = (
            "¡Hola! Bienvenido a PizzaBot 🍕 ¿Qué te apetece pedir?\n"
            "Puedes decírmelo todo junto, por ejemplo: "
            "'dos pepperoni familiares y una margarita mediana'."
        )
        return self._last_prompt

    def handle_message(self, text: str) -> str:
        text = text.strip()
        lowered = text.lower()

        if lowered in _BACK_COMMANDS:
            if not self._history:
                return "No hay ningún paso anterior al que volver."
            self.state, self._last_prompt = self._history.pop()
            return self._last_prompt

        if self.is_finished:
            return "Este pedido ya ha terminado. Escribe /start para empezar uno nuevo."

        self._history.append((self.state, self._last_prompt))
        handler = getattr(self, f"_handle_{self.state.name.lower()}")
        reply = handler(text)
        self._last_prompt = reply
        return reply

    @property
    def is_finished(self) -> bool:
        return self.state in (ConversationState.DONE, ConversationState.CANCELLED)

    @property
    def order(self) -> Order | None:
        if self.state != ConversationState.DONE:
            return None
        return self._data.get("order")

    # ---- Toma del pedido -------------------------------------------------

    def _handle_ask_order(self, text: str) -> str:
        lowered = text.lower()

        if "lleva" in lowered or "ingredientes" in lowered:
            for pizza, ingredients in PIZZA_INGREDIENTS.items():
                if pizza.value in lowered:
                    return f"La {pizza.value} lleva {ingredients}."
            return "Dime de qué pizza quieres saber los ingredientes."

        items = self._extract_items(text)
        if not items:
            if self._looks_like_menu_question(lowered):
                return self._menu_text()

            off_topic_reply = answer_off_topic(text)
            if off_topic_reply:
                return off_topic_reply

            opciones = ", ".join(p.value for p in PizzaType)
            return f"No te he entendido bien. Si quieres pedir, dime una pizza. Opciones: {opciones}"

        self._pending.extend(items)

        if len(items) > 1:
            resumen = ", ".join(it["pizza"].value for it in items)
            intro = f"Perfecto, he apuntado {len(items)} pizzas: {resumen}. Vamos a completar cada una.\n\n"
            return intro + self._advance_pending()

        return self._advance_pending()

    def _advance_pending(self) -> str:
        if self._pending:
            current = self._pending[0]
            pizza = current["pizza"]
            restantes = len(self._pending) - 1
            aviso = f" (quedan {restantes} pizza/s más por completar después de esta)" if restantes else ""

            if current.get("quantity") is None:
                self.state = ConversationState.ASK_ITEM_QUANTITY
                return f"¿Cuántas {pizza.value} quieres?{aviso}"

            if current.get("size") is None:
                self.state = ConversationState.ASK_ITEM_SIZE
                qty = current["quantity"]
                return f"{qty}x {pizza.value}. ¿Qué tamaño? individual, mediana o familiar{aviso}"

            self.state = ConversationState.ASK_ITEM_EXTRAS
            opciones = ", ".join(t.value for t in Topping)
            qty, size = current["quantity"], current["size"].value
            return (
                f"{qty}x {pizza.value} ({size}). ¿Algún ingrediente extra? {opciones}\n"
                f"(separa varios con comas, o escribe 'no'){aviso}"
            )

        self.state = ConversationState.ASK_MORE_PIZZA
        return f"{self._cart_summary()}\n¿Quieres añadir alguna pizza más? (sí/no)"

    def _handle_ask_item_quantity(self, text: str) -> str:
        qty = self._find_quantity(text.lower())
        if qty is None:
            return "Dime un número de unidades (por ejemplo: 2)"
        self._pending[0]["quantity"] = qty
        return self._advance_pending()

    def _handle_ask_item_size(self, text: str) -> str:
        size = self._extract_size(self._normalize_sizes(text).lower())
        if size is None:
            return "Elige un tamaño: individual, mediana o familiar"
        self._pending[0]["size"] = size
        return self._advance_pending()

    def _handle_ask_item_extras(self, text: str) -> str:
        lowered = text.lower()
        extras: list[Topping] = []
        if lowered != "no":
            extras = self._extract_toppings(lowered)
            if not extras:
                opciones = ", ".join(t.value for t in Topping)
                return f"No he reconocido ningún extra. Opciones: {opciones} (o escribe 'no')"

        current = self._pending.pop(0)
        item = CartItem(
            pizza=current["pizza"], size=current["size"], quantity=current["quantity"], extras=extras
        )
        self._items.append(item)
        return self._advance_pending()

    def _handle_ask_more_pizza(self, text: str) -> str:
        lowered = text.lower()
        if lowered in ("si", "sí"):
            self.state = ConversationState.ASK_ORDER
            return "Cuéntame qué otra pizza quieres."

        self.state = ConversationState.ASK_DRINKS
        opciones = ", ".join(DRINK_DISPLAY_NAMES[d] for d in Drink)
        return (
            "¿Quieres alguna bebida? Dime cuál y cuántas (ej: '2 cervezas'), "
            f"o escribe 'no' para seguir.\nBebidas: {opciones}"
        )

    def _handle_ask_drinks(self, text: str) -> str:
        lowered = text.lower()
        if lowered == "no":
            self.state = ConversationState.ASK_NOTES
            return "¿Alguna alergia o petición especial? (o escribe 'no')"

        selections = self._extract_drinks(text)
        if not selections:
            opciones = ", ".join(DRINK_DISPLAY_NAMES[d] for d in Drink)
            return f"No he reconocido esa bebida. Opciones: {opciones} (o escribe 'no' para seguir)"

        self._drinks.extend(selections)
        resumen = ", ".join(f"{s.quantity}x {DRINK_DISPLAY_NAMES[s.drink]}" for s in selections)
        return f"Apuntadas: {resumen} 🥤 ¿Otra bebida? o escribe 'no' para seguir."

    def _handle_ask_notes(self, text: str) -> str:
        lowered = text.lower()
        self._data["notes"] = None if lowered == "no" else text
        self.state = ConversationState.ASK_NAME
        return "Ya casi está 🙂 ¿A nombre de quién pongo el pedido?"

    def _handle_ask_name(self, text: str) -> str:
        if not text:
            return "¿A nombre de quién pongo el pedido?"
        self._data["customer_name"] = text
        self.state = ConversationState.ASK_ADDRESS
        return f"Genial, {text.capitalize()}. ¿A qué dirección lo enviamos?"

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
        total = order_total(order)
        return (
            "Repito tu pedido para confirmar:\n\n"
            f"{order.summary()}\n💶 Total: {total}€\n\n¿Confirmamos? (sí/no)"
        )

    def _handle_confirm(self, text: str) -> str:
        lowered = text.lower()
        if lowered in ("si", "sí"):
            self.state = ConversationState.DONE
            return "🍕 Pedido confirmado. ¡En camino!"
        self.state = ConversationState.CANCELLED
        return "Pedido cancelado. Escribe /start si quieres hacer otro."

    # ---- Extracción y ayudantes -----------------------------------------

    def _extract_items(self, text: str) -> list[dict]:
        normalized = self._normalize_sizes(text)
        extracted = extract_order_info(normalized)
        items: list[dict] = []
        if extracted and extracted.items:
            for ei in extracted.items:
                if ei.pizza is not None:
                    items.append({"pizza": ei.pizza, "size": ei.size, "quantity": ei.quantity})

        if not items:
            lowered = normalized.lower()
            for pizza in PizzaType:
                if pizza.value in lowered:
                    items.append({"pizza": pizza, "size": None, "quantity": None})

        return items

    def _cart_summary(self) -> str:
        lines = []
        for item in self._items:
            extras_txt = f" + {', '.join(e.value for e in item.extras)}" if item.extras else ""
            lines.append(f"{item.quantity}x {item.pizza.value} ({item.size.value}){extras_txt}")
        return "Llevas: " + "; ".join(lines)

    @staticmethod
    def _looks_like_menu_question(lowered: str) -> bool:
        return any(k in lowered for k in _MENU_KEYWORDS)

    @staticmethod
    def _menu_text() -> str:
        lineas = [f"- {p.value}: {PIZZA_INGREDIENTS[p]}" for p in PizzaType]
        return "Estas son nuestras pizzas:\n" + "\n".join(lineas) + "\n\n¿Cuál te apetece?"

    @staticmethod
    def _normalize_sizes(text: str) -> str:
        result = text
        for synonym, canonical in _SIZE_SYNONYMS.items():
            result = re.sub(rf"\b{synonym}\b", canonical, result, flags=re.IGNORECASE)
        return result

    @staticmethod
    def _normalize_drinks(text: str) -> str:
        result = text
        for synonym, canonical in _DRINK_SYNONYMS.items():
            result = re.sub(rf"\b{re.escape(synonym)}\b", canonical, result, flags=re.IGNORECASE)
        return result

    def _extract_drinks(self, text: str) -> list[DrinkSelection]:
        """Reconoce varias bebidas en un mismo mensaje ('una cerveza y una
        cocacola'), separando por comas y conjunciones. No usa IA aquí a
        propósito: el catálogo de bebidas es pequeño y cerrado, así que
        reglas simples bastan y evitan una llamada de red innecesaria.
        """
        normalized = self._normalize_drinks(text.lower())
        chunks = [c.strip() for c in _DRINK_SPLIT_RE.split(normalized) if c.strip()]
        if not chunks:
            chunks = [normalized]

        selections: list[DrinkSelection] = []
        for chunk in chunks:
            drink = self._extract_drink(chunk)
            if drink is None:
                continue
            qty = self._find_quantity(chunk) or 1
            selections.append(DrinkSelection(drink=drink, quantity=qty))
        return selections

    @staticmethod
    def _extract_size(lowered: str) -> Size | None:
        for size in Size:
            if size.value in lowered:
                return size
        return None

    @staticmethod
    def _find_quantity(lowered: str) -> int | None:
        match = re.search(r"\d+", lowered)
        if match:
            qty = int(match.group())
            return qty if 0 < qty <= 20 else None
        for word, num in _WORD_NUMBERS.items():
            if word in lowered.split():
                return num
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
            order = Order(
                customer_name=self._data["customer_name"],
                items=self._items,
                drinks=self._drinks,
                address=self._data["address"],
                notes=self._data.get("notes"),
            )
            return order, None
        except ValidationError as exc:
            return None, str(exc)