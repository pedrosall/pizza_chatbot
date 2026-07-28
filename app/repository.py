"""
Repositorio de pedidos: la única capa que sabe hablar con la base de datos.

Patrón clave: cada función acepta un `session_factory` opcional. En
producción usan la de app/db.py (SQLite real); en los tests le pasamos
una fábrica apuntando a una base de datos en memoria. Así probamos la
lógica de guardado/lectura sin tocar el archivo pizzabot.db real ni
depender de su estado previo.
"""

from __future__ import annotations

from app.catalog import order_total
from app.db import SessionLocal
from app.db_models import OrderRecord
from app.models import Order


def save_order(order: Order, session_factory=None) -> OrderRecord:
    session_factory = session_factory or SessionLocal
    total = order_total(
        order.item.pizza, order.item.size, order.item.quantity, order.item.extras, order.drink
    )
    record = OrderRecord(
        customer_name=order.customer_name,
        pizza=order.item.pizza.value,
        size=order.item.size.value,
        quantity=order.item.quantity,
        extras=",".join(e.value for e in order.item.extras),
        drink=order.drink.value if order.drink else None,
        notes=order.notes,
        address=order.address,
        total_price=total,
    )
    with session_factory() as session:
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def list_orders(session_factory=None) -> list[OrderRecord]:
    session_factory = session_factory or SessionLocal
    with session_factory() as session:
        return list(
            session.query(OrderRecord).order_by(OrderRecord.created_at.desc()).all()
        )