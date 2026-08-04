"""Fixtures para testes de integracao do modulo inteligencia."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.inteligencia.repository import IndicadorRepository, MedicaoIndicadorRepository
from app.inteligencia.schemas import (
    IndicadorCreateSchema,
    IndicadorReadSchema,
    MedicaoIndicadorCreateSchema,
)
from app.inteligencia.service import InteligenciaService

pytestmark = pytest.mark.integration

INTELIGENCIA_TABLES = (
    "medicao_indicador",
    "indicador",
)


@pytest.fixture(scope="session", autouse=True)
def require_inteligencia_schema(db_engine) -> None:
    with db_engine.connect() as conn:
        missing = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('indicador', 'medicao_indicador', 'safra')
                """
            )
        ).fetchall()
    if len(missing) < 3:
        pytest.skip(
            "Schema de inteligencia nao encontrado. Execute as migracoes antes dos testes."
        )


@pytest.fixture(autouse=True)
def clean_inteligencia_data(db_engine) -> Generator[None, None, None]:
    tables = ", ".join(INTELIGENCIA_TABLES)
    with db_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def indicador_repository() -> IndicadorRepository:
    return IndicadorRepository()


@pytest.fixture
def medicao_repository() -> MedicaoIndicadorRepository:
    return MedicaoIndicadorRepository()


@pytest.fixture
def inteligencia_service(
    indicador_repository: IndicadorRepository,
    medicao_repository: MedicaoIndicadorRepository,
) -> InteligenciaService:
    return InteligenciaService(
        indicador_repo=indicador_repository,
        medicao_repo=medicao_repository,
    )


@pytest.fixture
def id_safra(db_engine, unique_suffix: str) -> int:
    with db_engine.begin() as conn:
        return conn.execute(
            text(
                """
                INSERT INTO safra (nome, ano, status)
                VALUES (:nome, :ano, 'PLANEJADA')
                RETURNING id_safra
                """
            ),
            {"nome": f"Safra Teste {unique_suffix}", "ano": date.today().year},
        ).scalar_one()


@pytest.fixture
def sample_indicador(
    indicador_repository: IndicadorRepository,
    unique_suffix: str,
) -> IndicadorReadSchema:
    return indicador_repository.create_indicador(
        IndicadorCreateSchema(
            nome=f"Produtividade {unique_suffix}",
            unidade="kg/ha",
        )
    )


@pytest.fixture
def sample_medicao(
    medicao_repository: MedicaoIndicadorRepository,
    sample_indicador: IndicadorReadSchema,
    id_safra: int,
) -> dict:
    medicao = medicao_repository.create_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("100.50"),
            data_referencia=date.today(),
        )
    )
    return medicao.model_dump()
