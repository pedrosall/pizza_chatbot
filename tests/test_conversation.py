"""
Tests de la máquina de estados.

Nota didáctica: como Conversation no depende de Telegram ni de ningún
servicio externo, estos tests son rápidos, deterministas y no requieren
red. Por eso mockeamos `extract_order_info`: sin el mock, cada test que
pasa por ASK_PIZZA haría una llamada real a la API de Gemini (lento,
frágil ante cortes de red o cuota, y no determinista). Con
`return_value=None` simulamos "la IA no aportó nada", forzando el mismo
camino por reglas de keywords que estos tests ya validaban en la Fase 0.

Importante: mockeamos "app.conversation.extract_order_info" (donde se
usa), no "app.ai_extractor.extract_order_info" (donde se define). Al
hacer `from app.ai_extractor import extract_order_info` dentro de
conversation.py, ese nombre queda enganchado también al módulo
`app.conversation`, así que hay que interceptarlo ahí.
"""

from unittest.mock import patch

from app.conversation import Conversation, ConversationState


@patch("app.conversation.extract_order_info", return_value=None)
def test_happy_path_completes_order(mock_extract):
    convo = Conversation()

    reply = convo.handle_message("Pedro")
    assert "Pedro" in reply
    assert convo.state == ConversationState.ASK_PIZZA

    reply = convo.handle_message("quiero una carbonara")
    assert "carbonara" in reply.lower()
    assert convo.state == ConversationState.ASK_SIZE

    reply = convo.handle_message("familiar")
    assert convo.state == ConversationState.ASK_QUANTITY

    reply = convo.handle_message("2")
    assert convo.state == ConversationState.ASK_EXTRAS

    reply = convo.handle_message("bacon y queso extra")
    assert convo.state == ConversationState.ASK_DRINK

    reply = convo.handle_message("cerveza")
    assert convo.state == ConversationState.ASK_NOTES

    reply = convo.handle_message("sin cebolla por favor")
    assert convo.state == ConversationState.ASK_ADDRESS

    reply = convo.handle_message("Calle Falsa 123, Madrid")
    assert "Total" in reply
    assert convo.state == ConversationState.CONFIRM

    reply = convo.handle_message("sí")
    assert convo.is_finished
    assert convo.state == ConversationState.DONE


@patch("app.conversation.extract_order_info", return_value=None)
def test_cancel_at_confirmation(mock_extract):
    convo = Conversation()
    convo.handle_message("Ana")
    convo.handle_message("pepperoni")
    convo.handle_message("familiar")
    convo.handle_message("1")
    convo.handle_message("no")   # sin extras
    convo.handle_message("no")   # sin bebida
    convo.handle_message("no")   # sin notas
    convo.handle_message("Calle Real 5")

    reply = convo.handle_message("no")
    assert convo.is_finished
    assert convo.state == ConversationState.CANCELLED
    assert "cancelado" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_invalid_pizza_does_not_advance_state(mock_extract):
    convo = Conversation()
    convo.handle_message("Luis")
    reply = convo.handle_message("quiero una pizza de piña con nata")
    assert convo.state == ConversationState.ASK_PIZZA
    assert "no tenemos" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_ingredient_question_does_not_consume_pizza_slot(mock_extract):
    convo = Conversation()
    convo.handle_message("Marta")
    reply = convo.handle_message("¿qué lleva la vegetariana?")
    assert "champiñones" in reply.lower()
    assert convo.state == ConversationState.ASK_PIZZA


@patch("app.conversation.extract_order_info", return_value=None)
def test_invalid_quantity_reprompts(mock_extract):
    convo = Conversation()
    convo.handle_message("Iker")
    convo.handle_message("hawaiana")
    convo.handle_message("individual")
    reply = convo.handle_message("muchas")
    assert convo.state == ConversationState.ASK_QUANTITY
    assert "número" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_word_number_for_quantity(mock_extract):
    convo = Conversation()
    convo.handle_message("Iker")
    convo.handle_message("hawaiana")
    convo.handle_message("individual")
    convo.handle_message("una")
    assert convo.state == ConversationState.ASK_EXTRAS


@patch("app.conversation.extract_order_info", return_value=None)
def test_extras_multiple_toppings_no_duplicates(mock_extract):
    convo = Conversation()
    convo.handle_message("Nora")
    convo.handle_message("margarita")
    convo.handle_message("mediana")
    convo.handle_message("1")
    convo.handle_message("bacon, bacon y aceitunas")
    order_item_extras = convo._data["extras"]
    assert len(order_item_extras) == 2  # bacon no se duplica


@patch("app.conversation.extract_order_info", return_value=None)
def test_unrecognized_extra_reprompts(mock_extract):
    convo = Conversation()
    convo.handle_message("Nora")
    convo.handle_message("margarita")
    convo.handle_message("mediana")
    convo.handle_message("1")
    reply = convo.handle_message("piña")  # no es un Topping válido
    assert convo.state == ConversationState.ASK_EXTRAS
    assert "no he reconocido" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_order_property_only_available_when_done(mock_extract):
    convo = Conversation()
    assert convo.order is None  # todavía no hay pedido

    convo.handle_message("Leo")
    convo.handle_message("hawaiana")
    convo.handle_message("individual")
    convo.handle_message("1")
    convo.handle_message("no")
    convo.handle_message("no")
    convo.handle_message("no")
    convo.handle_message("Calle Test 9")
    assert convo.order is None  # en CONFIRM, todavía no confirmado

    convo.handle_message("sí")
    assert convo.order is not None
    assert convo.order.customer_name == "Leo"