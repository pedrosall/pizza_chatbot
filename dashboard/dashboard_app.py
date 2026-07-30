"""
Dashboard de administración, en Streamlit.

Igual que bot/telegram_bot.py, esta es una capa FINA: solo lee datos a
través de app/repository.py (la misma capa que usa el bot) y los
presenta. No accede a la base de datos directamente ni duplica lógica
de negocio -- si mañana migramos a Postgres, este archivo no cambia.
"""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.repository import list_orders

from app.db import init_db
from app.repository import list_orders

init_db()

st.set_page_config(page_title="PizzaBot Admin", page_icon="🍕", layout="wide")

st.title("🍕 PizzaBot — Panel de administración")

if st.button("🔄 Actualizar"):
    st.rerun()

orders = list_orders()

if not orders:
    st.info("Todavía no hay pedidos registrados.")
    st.stop()

# ---- Métricas rápidas ------------------------------------------------

total_pedidos = len(orders)
ingresos_totales = sum(o.total_price for o in orders)
ticket_medio = ingresos_totales / total_pedidos

col1, col2, col3 = st.columns(3)
col1.metric("Pedidos totales", total_pedidos)
col2.metric("Ingresos totales", f"{ingresos_totales:.2f} €")
col3.metric("Ticket medio", f"{ticket_medio:.2f} €")

st.divider()

# ---- Tabla de pedidos recientes ---------------------------------------

st.subheader("Pedidos recientes")


def _resumen_pizzas(items_json: str) -> str:
    items = json.loads(items_json)
    return ", ".join(f"{i['quantity']}x {i['pizza']} ({i['size']})" for i in items)


def _resumen_bebidas(drinks_json: str) -> str:
    drinks = json.loads(drinks_json)
    if not drinks:
        return "—"
    return ", ".join(f"{d['quantity']}x {d['drink']}" for d in drinks)


tabla = pd.DataFrame(
    {
        "Fecha": [o.created_at.strftime("%d/%m %H:%M") for o in orders],
        "Cliente": [o.customer_name for o in orders],
        "Pizzas": [_resumen_pizzas(o.items_json) for o in orders],
        "Bebidas": [_resumen_bebidas(o.drinks_json) for o in orders],
        "Dirección": [o.address for o in orders],
        "Total (€)": [o.total_price for o in orders],
    }
)

st.dataframe(tabla, use_container_width=True, hide_index=True)

st.divider()

# ---- Gráfico: pizzas más pedidas --------------------------------------

st.subheader("Pizzas más pedidas")

conteo: dict[str, int] = {}
for o in orders:
    for item in json.loads(o.items_json):
        conteo[item["pizza"]] = conteo.get(item["pizza"], 0) + item["quantity"]

if conteo:
    df_conteo = (
        pd.DataFrame(list(conteo.items()), columns=["Pizza", "Unidades vendidas"])
        .sort_values("Unidades vendidas", ascending=False)
        .set_index("Pizza")
    )
    st.bar_chart(df_conteo)