"""Tests de la máquina de estados (flujo estilo pizzería real, Fase 3.6)."""

from unittest.mock import patch

from app.conversation import Conversation, ConversationState


@patch("app.conversation.extract_order_info", return_value=None)
def test_single_pizza_full_flow(mock_extract):
    convo = Conversation()
    convo.greeting()
    assert convo.state == ConversationState.ASK_ORDER

    convo.handle_message("carbonara")
    assert convo.state == ConversationState.ASK_ITEM_QUANTITY

    convo.handle_message("2")
    assert convo.state == ConversationState.ASK_ITEM_SIZE

    convo.handle_message("familiar")
    assert convo.state == ConversationState.ASK_ITEM_EXTRAS

    convo.handle_message("bacon")
    assert convo.state == ConversationState.ASK_MORE_PIZZA

    convo.handle_message("no")
    assert convo.state == ConversationState.ASK_DRINKS

    convo.handle_message("no")
    assert convo.state == ConversationState.ASK_NOTES

    convo.handle_message("no")
    assert convo.state == ConversationState.ASK_NAME

    convo.handle_message("Pedro")
    assert convo.state == ConversationState.ASK_ADDRESS

    reply = convo.handle_message("Calle Falsa 123")
    assert "Repito tu pedido" in reply
    assert convo.state == ConversationState.CONFIRM

    convo.handle_message("sí")
    assert convo.state == ConversationState.DONE
    assert convo.order.customer_name == "Pedro"


@patch("app.conversation.extract_order_info", return_value=None)
def test_two_pizzas_mentioned_in_one_message_both_captured(mock_extract):
    convo = Conversation()
    convo.handle_message("quiero una pepperoni y una vegetariana")

    assert len(convo._pending) == 2
    assert convo._pending[0]["pizza"].value == "pepperoni"
    assert convo._pending[1]["pizza"].value == "vegetariana"

    convo.handle_message("1")
    convo.handle_message("mediana")
    convo.handle_message("no")
    assert len(convo._items) == 1
    assert len(convo._pending) == 1

    convo.handle_message("2")
    convo.handle_message("familiar")
    convo.handle_message("no")
    assert len(convo._items) == 2
    assert convo.state == ConversationState.ASK_MORE_PIZZA


@patch("app.conversation.extract_order_info", return_value=None)
def test_multiple_drinks_with_quantities(mock_extract):
    convo = Conversation()
    convo.handle_message("hawaiana")
    convo.handle_message("1")
    convo.handle_message("individual")
    convo.handle_message("no")
    convo.handle_message("no")

    convo.handle_message("3 cervezas")
    convo.handle_message("1 agua")
    convo.handle_message("no")

    assert len(convo._drinks) == 2
    assert convo._drinks[0].quantity == 3
    assert convo._drinks[1].quantity == 1


@patch("app.conversation.extract_order_info", return_value=None)
def test_back_command_returns_to_previous_prompt(mock_extract):
    convo = Conversation()
    convo.handle_message("margarita")
    prompt_before = convo._last_prompt

    convo.handle_message("2")
    assert convo.state == ConversationState.ASK_ITEM_SIZE

    reply = convo.handle_message("atrás")
    assert convo.state == ConversationState.ASK_ITEM_QUANTITY
    assert reply == prompt_before


@patch("app.conversation.extract_order_info", return_value=None)
def test_back_command_with_no_history_is_safe(mock_extract):
    convo = Conversation()
    reply = convo.handle_message("atrás")
    assert "no hay ningún paso anterior" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_cancel_at_confirmation(mock_extract):
    convo = Conversation()
    convo.handle_message("pepperoni")
    convo.handle_message("1")
    convo.handle_message("familiar")
    convo.handle_message("no")
    convo.handle_message("no")
    convo.handle_message("no")
    convo.handle_message("no")
    convo.handle_message("Ana")
    convo.handle_message("Calle Real 5")

    reply = convo.handle_message("no")
    assert convo.state == ConversationState.CANCELLED
    assert "cancelado" in reply.lower()


@patch("app.conversation.answer_off_topic", return_value=None)
@patch("app.conversation.extract_order_info", return_value=None)
def test_invalid_pizza_does_not_advance(mock_extract, mock_faq):
    convo = Conversation()
    reply = convo.handle_message("quiero una pizza de piña con nata")
    assert convo.state == ConversationState.ASK_ORDER
    assert "no te he entendido bien" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_ingredient_question_does_not_start_an_order(mock_extract):
    convo = Conversation()
    reply = convo.handle_message("¿qué lleva la vegetariana?")
    assert "champiñones" in reply.lower()
    assert convo.state == ConversationState.ASK_ORDER
    assert not convo._pending


@patch("app.conversation.extract_order_info", return_value=None)
def test_unrecognized_extra_reprompts(mock_extract):
    convo = Conversation()
    convo.handle_message("margarita")
    convo.handle_message("1")
    convo.handle_message("mediana")
    reply = convo.handle_message("piña")
    assert convo.state == ConversationState.ASK_ITEM_EXTRAS
    assert "no he reconocido" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_menu_question_shows_menu_not_error(mock_extract):
    convo = Conversation()
    reply = convo.handle_message("¿qué pizzas tenéis?")
    assert "nuestras pizzas" in reply.lower()
    assert "carbonara" in reply.lower()
    assert convo.state == ConversationState.ASK_ORDER


@patch("app.conversation.extract_order_info", return_value=None)
@patch(
    "app.conversation.answer_off_topic",
    return_value="¡Buena pregunta! Tardamos unos 30-40 min. ¿Empezamos tu pedido?",
)
def test_off_topic_question_gets_helpful_reply_not_error(mock_faq, mock_extract):
    convo = Conversation()
    reply = convo.handle_message("¿cuánto tardáis en traer la pizza?")
    assert "30-40" in reply
    assert convo.state == ConversationState.ASK_ORDER


@patch("app.conversation.extract_order_info", return_value=None)
@patch("app.conversation.answer_off_topic", return_value=None)
def test_off_topic_falls_back_when_ai_unavailable(mock_faq, mock_extract):
    convo = Conversation()
    reply = convo.handle_message("cuéntame un chiste")
    assert "no te he entendido bien" in reply.lower()

@patch("app.conversation.extract_order_info", return_value=None)
def test_multiple_pizzas_detected_gets_explicit_confirmation(mock_extract):
    convo = Conversation()
    reply = convo.handle_message("una pepperoni y una vegetariana")
    assert "2 pizzas" in reply
    assert "quedan 1 pizza" in reply.lower()

@patch("app.conversation.extract_order_info", return_value=None)
def test_size_synonym_grande_maps_to_familiar(mock_extract):
    convo = Conversation()
    convo.handle_message("margarita")
    convo.handle_message("1")
    reply = convo.handle_message("grande")
    assert convo.state == ConversationState.ASK_ITEM_EXTRAS
    assert "familiar" in reply.lower()


@patch("app.conversation.extract_order_info", return_value=None)
def test_size_synonym_pequena_maps_to_individual(mock_extract):
    convo = Conversation()
    convo.handle_message("margarita")
    convo.handle_message("1")
    reply = convo.handle_message("pequeña")
    assert convo.state == ConversationState.ASK_ITEM_EXTRAS
    assert "individual" in reply.lower()