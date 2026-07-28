"""
Tests del repositorio.

Usamos una base de datos SQLite EN MEMORIA (":memory:"), exclusiva para
estos tests, en vez del archivo pizzabot.db real. Así los tests no
ensucian tus datos de desarrollo ni dependen de qué haya en el archivo
en ese momento — cada test empieza con una base de datos limpia.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Drink, Order, OrderItem, PizzaType, Size, Topping
from app.repository import list_orders, save_order


@pytest.fixture
def test_session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _sample_order() -> Order:
    return Order(
        customer_name="Ana",
        item=OrderItem(
            pizza=PizzaType.MARGARITA, size=Size.MEDIANA, quantity=2, extras=[Topping.BACON]
        ),
        drink=Drink.COLA,
        address="Calle Falsa 123",
    )


def test_save_order_persists_correct_data(test_session_factory):
    record = save_order(_sample_order(), session_factory=test_session_factory)

    assert record.id is not None
    assert record.customer_name == "Ana"
    assert record.pizza == "margarita"
    assert record.extras == "bacon"
    assert record.total_price > 0


def test_list_orders_returns_saved_orders(test_session_factory):
    save_order(_sample_order(), session_factory=test_session_factory)
    save_order(_sample_order(), session_factory=test_session_factory)

    orders = list_orders(session_factory=test_session_factory)
    assert len(orders) == 2