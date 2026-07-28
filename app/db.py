"""
Configuración de la base de datos.

SQLite guarda todo en un único archivo (pizzabot.db) que se crea solo
al arrancar. No hace falta instalar ni levantar ningún servidor de base
de datos — ideal para desarrollo y portfolio. El día que quieras migrar
a Postgres, solo cambia DATABASE_URL; el resto del código no se entera.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos de tabla (ORM)."""


DATABASE_URL = "sqlite:///pizzabot.db"

engine = create_engine(DATABASE_URL, echo=False)

# sessionmaker crea una "fábrica" de sesiones; cada sesión es una
# conversación temporal con la base de datos (abrir, operar, cerrar).
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Crea las tablas si no existen. Se llama una vez al arrancar el bot."""
    from app import db_models  # noqa: F401 — importa para registrar las tablas

    Base.metadata.create_all(engine)