"""Fixtures para testes de integracao do modulo manutencao."""

from __future__ import annotations

import logging
from collections.abc import Generator

import pytest
from sqlalchemy import text

from app.manutencao.repository import ManutencaoRepository
from app.manutencao.schemas.maquina import MaquinaCreateSchema, MaquinaReadSchema
from app.manutencao.schemas.manutencao import ManutencaoCreateSchema
from app.manutencao.service import ManutencaoService

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.integration

MANUTENCAO_TABLES = (
    "pagamento",
    "conta_pagar",
    "historico_manutencao",
    "fluxo_caixa",
    "ordem_servico",
    "manutencao_preventiva",
    "manutencao_corretiva",
    "manutencao",
    "plano_manutencao",
    "abastecimento",
    "uso_maquina",
    "maquina",
    "prestador_servico",
    "tipo_maquina",
)


@pytest.fixture(scope="session", autouse=True)
def require_manutencao_schema(db_engine) -> None:
    with db_engine.connect() as conn:
        missing = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('maquina', 'manutencao', 'ordem_servico')
                """
            )
        ).fetchall()
    if len(missing) < 3:
        pytest.skip(
            "Schema de manutencao nao encontrado. Execute as migracoes antes dos testes."
        )


@pytest.fixture(autouse=True)
def clean_manutencao_data(db_engine) -> Generator[None, None, None]:
    tables = ", ".join(MANUTENCAO_TABLES)
    with db_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def manutencao_repository(pg_connector) -> ManutencaoRepository:
    return ManutencaoRepository(pg_connector, logger)


@pytest.fixture
def manutencao_service(manutencao_repository) -> ManutencaoService:
    return ManutencaoService(repository=manutencao_repository)


@pytest.fixture
def id_fazenda(db_engine, unique_suffix: str) -> int:
    with db_engine.begin() as conn:
        return conn.execute(
            text(
                """
                INSERT INTO fazenda (nome, localizacao)
                VALUES (:nome, :localizacao)
                RETURNING id_fazenda
                """
            ),
            {
                "nome": f"Fazenda Teste {unique_suffix}",
                "localizacao": "Area de testes",
            },
        ).scalar_one()


@pytest.fixture
def id_tipo_maquina(db_engine, unique_suffix: str) -> int:
    with db_engine.begin() as conn:
        return conn.execute(
            text(
                """
                INSERT INTO tipo_maquina (descricao)
                VALUES (:descricao)
                RETURNING id_tipo_maquina
                """
            ),
            {"descricao": f"Tipo {unique_suffix}"},
        ).scalar_one()


@pytest.fixture
def sample_maquina(
    manutencao_repository: ManutencaoRepository,
    id_fazenda: int,
    id_tipo_maquina: int,
    unique_suffix: str,
) -> MaquinaReadSchema:
    maquina = manutencao_repository.create_maquina(
        MaquinaCreateSchema(
            id_tipo_maquina=id_tipo_maquina,
            nome=f"Trator {unique_suffix}",
            status="DISPONIVEL",
        ),
        id_fazenda=id_fazenda,
    )
    assert maquina is not None
    return maquina


@pytest.fixture
def sample_plano(db_engine, sample_maquina: MaquinaReadSchema) -> int:
    with db_engine.begin() as conn:
        return conn.execute(
            text(
                """
                INSERT INTO plano_manutencao (id_maquina, periodicidade)
                VALUES (:id_maquina, :periodicidade)
                RETURNING id_plano
                """
            ),
            {
                "id_maquina": sample_maquina.id_maquina,
                "periodicidade": "90 DIAS",
            },
        ).scalar_one()


@pytest.fixture
def manutencao_aberta(
    manutencao_repository: ManutencaoRepository,
    sample_maquina: MaquinaReadSchema,
) -> int:
    result = manutencao_repository.create_manutencao_corretiva(
        ManutencaoCreateSchema(
            id_maquina=sample_maquina.id_maquina,
            status="ABERTA",
            tipo="CORRETIVA",
        ),
        defeito_relatado="Vazamento de oleo",
    )
    assert result is not None
    manutencao, _ = result
    return manutencao.id_manutencao
