"""Fixtures compartilhadas para testes de integracao."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.core.database import PgConnector
from app.identity.repository import IdentityRepository
from app.identity.service import IdentityService

logger = logging.getLogger(__name__)

IDENTITY_TABLES = (
    "identidade_externa",
    "usuario_perfil",
    "auditoria_log",
    "notificacao",
    "usuario",
    "email",
    "telefone",
    "funcionario",
    "cliente",
    "fornecedor",
    "pessoa",
)


def _database_available() -> bool:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def db_engine():
    if not _database_available():
        pytest.skip("PostgreSQL indisponivel. Suba o docker compose antes de rodar os testes.")
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        if conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'pessoa'"
            )
        ).fetchone() is None:
            pytest.skip("Schema de identidade nao encontrado. Execute as migracoes antes dos testes.")
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_identity_data(db_engine) -> Generator[None, None, None]:
    tables = ", ".join(IDENTITY_TABLES)
    with db_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def pg_connector(db_engine) -> PgConnector:
    return PgConnector(db_engine)


@pytest.fixture
def identity_repository(pg_connector) -> IdentityRepository:
    return IdentityRepository(pg_connector, logger)


@pytest.fixture
def identity_service(identity_repository) -> IdentityService:
    return IdentityService(repository=identity_repository)


@pytest.fixture
def unique_suffix() -> str:
    return uuid.uuid4().hex[:12]


@pytest.fixture
def sample_person_data(unique_suffix: str) -> dict[str, str]:
    return {
        "nome": f"Usuario Teste {unique_suffix}",
        "documento": f"doc-{unique_suffix}",
        "email": f"user-{unique_suffix}@example.com",
    }
