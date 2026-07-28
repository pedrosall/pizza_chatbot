"""
Tests de la máquina de estados.

Nota didáctica: como Conversation no depende de Telegram ni de ningún
servicio externo, estos tests son rápidos, deterministas y no requieren
mocks. Este es el beneficio directo de haber separado bien las capas.
"""

from app.conversation import Conversation, ConversationState


def test_happy_path_completes_order():
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


def test_cancel_at_confirmation():
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


def test_invalid_pizza_does_not_advance_state():
    convo = Conversation()
    convo.handle_message("Luis")
    reply = convo.handle_message("quiero una pizza de piña con nata")
    assert convo.state == ConversationState.ASK_PIZZA
    assert "no tenemos" in reply.lower()


def test_ingredient_question_does_not_consume_pizza_slot():
    convo = Conversation()
    convo.handle_message("Marta")
    reply = convo.handle_message("¿qué lleva la vegetariana?")
    assert "champiñones" in reply.lower()
    assert convo.state == ConversationState.ASK_PIZZA


def test_invalid_quantity_reprompts():
    convo = Conversation()
    convo.handle_message("Iker")
    convo.handle_message("hawaiana")
    convo.handle_message("individual")
    reply = convo.handle_message("muchas")
    assert convo.state == ConversationState.ASK_QUANTITY
    assert "número" in reply.lower()


def test_word_number_for_quantity():
    convo = Conversation()
    convo.handle_message("Iker")
    convo.handle_message("hawaiana")
    convo.handle_message("individual")
    convo.handle_message("una")
    assert convo.state == ConversationState.ASK_EXTRAS


def test_extras_multiple_toppings_no_duplicates():
    convo = Conversation()
    convo.handle_message("Nora")
    convo.handle_message("margarita")
    convo.handle_message("mediana")
    convo.handle_message("1")
    convo.handle_message("bacon, bacon y aceitunas")
    order_item_extras = convo._data["extras"]
    assert len(order_item_extras) == 2  # bacon no se duplica


def test_unrecognized_extra_reprompts():
    convo = Conversation()
    convo.handle_message("Nora")
    convo.handle_message("margarita")
    convo.handle_message("mediana")
    convo.handle_message("1")
    reply = convo.handle_message("piña")  # no es un Topping válido
    assert convo.state == ConversationState.ASK_EXTRAS
    assert "no he reconocido" in reply.lower()