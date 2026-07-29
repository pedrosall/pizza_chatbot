from __future__ import annotations

import json

from app.catalog import order_total
from app.db import SessionLocal
from app.db_models import OrderRecord
from app.models import Order


def save_order(order: Order, session_factory=None) -> OrderRecord:
    session_factory = session_factory or SessionLocal
    total = order_total(order)
    record = OrderRecord(
        customer_name=order.customer_name,
        items_json=json.dumps([item.model_dump(mode="json") for item in order.items]),
        drinks_json=json.dumps([d.model_dump(mode="json") for d in order.drinks]),
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
        return list(session.query(OrderRecord).order_by(OrderRecord.created_at.desc()).all())