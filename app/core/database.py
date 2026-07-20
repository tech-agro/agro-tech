"""Conexao com PostgreSQL via SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import create_engine, text

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

class PgConnector:

    def __init__(self, pool) -> None:
        self.pool = pool

pg_connector = PgConnector(engine)

def check_connection() -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Conexao com PostgreSQL ativa."
    except Exception as exc:
        return False, f"Falha na conexao: {exc}"
