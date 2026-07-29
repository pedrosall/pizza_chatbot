"""
Punto de entrada del bot de Telegram.

Esta es deliberadamente la capa MÁS FINA del proyecto: solo traduce
mensajes de Telegram <-> Conversation, y persiste el pedido cuando
termina. Toda la lógica de negocio real vive en app/, no aquí. Si mañana
quisiéramos exponer el mismo bot por WhatsApp o por una API REST, solo
haría falta escribir un archivo equivalente a este — app/ no cambiaría.
"""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from app.conversation import Conversation, ConversationState
from app.db import init_db
from app.repository import save_order

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Una Conversation por chat_id. En memoria: si el proceso se reinicia a
# mitad de una conversación, esa conversación concreta se pierde (pero
# los pedidos YA confirmados están a salvo en la base de datos, gracias
# a la Fase 2). Persistir conversaciones a medio hacer es una mejora
# posible a futuro, no algo que necesitemos ahora para un portfolio.
conversations: dict[int, Conversation] = {}

dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    conversations[message.chat.id] = Conversation()
    convo = conversations[message.chat.id]
    reply = convo.greeting()  # antes: convo.handle_message("")
    await message.answer(reply)


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    chat_id = message.chat.id
    if chat_id not in conversations:
        conversations[chat_id] = Conversation()

    convo = conversations[chat_id]
    reply = convo.handle_message(message.text)
    await message.answer(reply)

    if convo.state == ConversationState.DONE and convo.order is not None:
        record = save_order(convo.order)
        logger.info("Pedido #%s guardado para %s", record.id, record.customer_name)
        del conversations[chat_id]  # listo para un pedido nuevo si escribe otra vez
    elif convo.state == ConversationState.CANCELLED:
        del conversations[chat_id]


async def main() -> None:
    init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en tu .env")

    bot = Bot(token=token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())