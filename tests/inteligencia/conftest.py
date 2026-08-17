"""Fixtures para testes de integracao do modulo inteligencia."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.inteligencia.repository import (
    FitossanidadeBiRepository,
    IndicadorRepository,
    MedicaoIndicadorRepository,
    ProdutividadeRepository,
)
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

BI_TABLES = (
    "conta_pagar",
    "aplicacao_defensivo",
    "ocorrencia_agente",
    "controle_fitossanitario",
    "colheita",
    "plantio",
    "ordem_producao",
    "planejamento_safra",
    "talhao",
    "agente_nocivo",
    "insumo",
    "produto",
    "safra",
    "cultura",
    "fazenda",
    "funcionario",
    "pessoa",
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


@pytest.fixture(autouse=True)
def clean_bi_data(db_engine) -> Generator[None, None, None]:
    tables = ", ".join(BI_TABLES)
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


@pytest.fixture
def produtividade_repository() -> ProdutividadeRepository:
    return ProdutividadeRepository()


@pytest.fixture
def fitossanidade_bi_repository() -> FitossanidadeBiRepository:
    return FitossanidadeBiRepository()


@pytest.fixture
def cenario_bi(db_engine, unique_suffix: str) -> dict:
    """Monta talhao/safra/planejamento/plantio/colheita/fitossanidade minimos.

    Talhao A: meta 100 kg/ha, colhido 1000kg em 10ha -> realizado 100 kg/ha (0%).
    Talhao B: meta 200 kg/ha, colhido 3000kg em 20ha (sem area_planejada,
    usa talhao.area_hectares) -> realizado 150 kg/ha (-25%).
    Talhao A recebe 1 aplicacao de defensivo com custo e 1 ocorrencia (Alto).
    Talhao B nao recebe nenhum registro fitossanitario (custo/ocorrencias = 0).
    """
    with db_engine.begin() as conn:
        id_pessoa = conn.execute(
            text(
                "INSERT INTO pessoa (nome, documento) VALUES (:nome, :doc) "
                "RETURNING id_pessoa"
            ),
            {"nome": f"Func {unique_suffix}", "doc": f"doc-{unique_suffix}"},
        ).scalar_one()
        id_funcionario = conn.execute(
            text(
                "INSERT INTO funcionario (id_pessoa, cargo, setor) "
                "VALUES (:id_pessoa, 'Agronomo', 'Campo') RETURNING id_funcionario"
            ),
            {"id_pessoa": id_pessoa},
        ).scalar_one()

        id_fazenda = conn.execute(
            text("INSERT INTO fazenda (nome) VALUES (:nome) RETURNING id_fazenda"),
            {"nome": f"Fazenda {unique_suffix}"},
        ).scalar_one()
        id_cultura = conn.execute(
            text("INSERT INTO cultura (nome) VALUES (:nome) RETURNING id_cultura"),
            {"nome": f"Cultura {unique_suffix}"},
        ).scalar_one()

        id_categoria = conn.execute(
            text(
                "INSERT INTO categoria_produto (nome) VALUES (:nome) "
                "RETURNING id_categoria"
            ),
            {"nome": f"Categoria {unique_suffix}"},
        ).scalar_one()
        id_unidade = conn.execute(
            text(
                "INSERT INTO unidade_medida (sigla, descricao) VALUES (:sigla, :descricao) "
                "RETURNING id_unidade"
            ),
            {"sigla": f"L{unique_suffix[:4]}", "descricao": f"Litro {unique_suffix}"},
        ).scalar_one()
        id_produto = conn.execute(
            text(
                "INSERT INTO produto (id_categoria, id_unidade, nome, preco) "
                "VALUES (:id_categoria, :id_unidade, :nome, 20.00) RETURNING id_produto"
            ),
            {
                "id_categoria": id_categoria,
                "id_unidade": id_unidade,
                "nome": f"Insumo {unique_suffix}",
            },
        ).scalar_one()
        conn.execute(
            text("INSERT INTO insumo (id_produto) VALUES (:id_produto)"),
            {"id_produto": id_produto},
        )

        id_safra = conn.execute(
            text(
                "INSERT INTO safra (nome, ano, status) "
                "VALUES (:nome, :ano, 'EM_ANDAMENTO') RETURNING id_safra"
            ),
            {"nome": f"Safra BI {unique_suffix}", "ano": date.today().year},
        ).scalar_one()

        id_talhao_a = conn.execute(
            text(
                "INSERT INTO talhao (id_fazenda, id_safra, nome, area_hectares) "
                "VALUES (:id_fazenda, :id_safra, :nome, 10) RETURNING id_talhao"
            ),
            {"id_fazenda": id_fazenda, "id_safra": id_safra, "nome": f"Talhao A {unique_suffix}"},
        ).scalar_one()
        id_talhao_b = conn.execute(
            text(
                "INSERT INTO talhao (id_fazenda, id_safra, nome, area_hectares) "
                "VALUES (:id_fazenda, :id_safra, :nome, 20) RETURNING id_talhao"
            ),
            {"id_fazenda": id_fazenda, "id_safra": id_safra, "nome": f"Talhao B {unique_suffix}"},
        ).scalar_one()

        id_planejamento_a = conn.execute(
            text(
                "INSERT INTO planejamento_safra "
                "(id_safra, id_talhao, id_cultura, meta_produtividade, area_planejada, status) "
                "VALUES (:id_safra, :id_talhao, :id_cultura, 100, 10, 'EM_EXECUCAO') "
                "RETURNING id_planejamento"
            ),
            {"id_safra": id_safra, "id_talhao": id_talhao_a, "id_cultura": id_cultura},
        ).scalar_one()
        id_planejamento_b = conn.execute(
            text(
                "INSERT INTO planejamento_safra "
                "(id_safra, id_talhao, id_cultura, meta_produtividade, status) "
                "VALUES (:id_safra, :id_talhao, :id_cultura, 200, 'EM_EXECUCAO') "
                "RETURNING id_planejamento"
            ),
            {"id_safra": id_safra, "id_talhao": id_talhao_b, "id_cultura": id_cultura},
        ).scalar_one()

        id_ordem = conn.execute(
            text(
                "INSERT INTO ordem_producao (id_safra, status) "
                "VALUES (:id_safra, 'ABERTA') RETURNING id_ordem"
            ),
            {"id_safra": id_safra},
        ).scalar_one()

        def _novo_plantio(id_talhao: int, id_planejamento: int) -> int:
            return conn.execute(
                text(
                    "INSERT INTO plantio "
                    "(id_ordem, id_talhao, id_produto, id_cultura, id_planejamento, status) "
                    "VALUES (:id_ordem, :id_talhao, :id_produto, :id_cultura, "
                    ":id_planejamento, 'CONCLUIDO') RETURNING id_plantio"
                ),
                {
                    "id_ordem": id_ordem,
                    "id_talhao": id_talhao,
                    "id_produto": id_produto,
                    "id_cultura": id_cultura,
                    "id_planejamento": id_planejamento,
                },
            ).scalar_one()

        id_plantio_a1 = _novo_plantio(id_talhao_a, id_planejamento_a)
        id_plantio_a2 = _novo_plantio(id_talhao_a, id_planejamento_a)
        id_plantio_b = _novo_plantio(id_talhao_b, id_planejamento_b)

        def _nova_colheita(id_plantio: int, quantidade: str) -> None:
            conn.execute(
                text(
                    "INSERT INTO colheita (id_plantio, quantidade_colhida, status) "
                    "VALUES (:id_plantio, :quantidade, 'CONCLUIDA')"
                ),
                {"id_plantio": id_plantio, "quantidade": quantidade},
            )

        _nova_colheita(id_plantio_a1, "400")
        _nova_colheita(id_plantio_a2, "600")
        _nova_colheita(id_plantio_b, "3000")

        id_controle = conn.execute(
            text(
                "INSERT INTO controle_fitossanitario "
                "(id_plantio, id_funcionario, nivel_severidade) "
                "VALUES (:id_plantio, :id_funcionario, 'Alto') RETURNING id_controle"
            ),
            {"id_plantio": id_plantio_a1, "id_funcionario": id_funcionario},
        ).scalar_one()

        id_agente = conn.execute(
            text(
                "INSERT INTO agente_nocivo (nome_comum) VALUES (:nome) RETURNING id_agente"
            ),
            {"nome": f"Agente {unique_suffix}"},
        ).scalar_one()
        conn.execute(
            text(
                "INSERT INTO ocorrencia_agente (id_controle, id_agente, nivel_infestacao) "
                "VALUES (:id_controle, :id_agente, 'Alto')"
            ),
            {"id_controle": id_controle, "id_agente": id_agente},
        )

        id_aplicacao = conn.execute(
            text(
                "INSERT INTO aplicacao_defensivo "
                "(id_controle, id_insumo, volume_aplicado, dt_aplicacao) "
                "VALUES (:id_controle, :id_insumo, 25, CURRENT_DATE) RETURNING id_aplicacao"
            ),
            {"id_controle": id_controle, "id_insumo": id_produto},
        ).scalar_one()
        conn.execute(
            text(
                "INSERT INTO conta_pagar (id_aplicacao, valor, status) "
                "VALUES (:id_aplicacao, 500.00, 'ABERTA')"
            ),
            {"id_aplicacao": id_aplicacao},
        )

    return {
        "id_safra": id_safra,
        "id_talhao_a": id_talhao_a,
        "id_talhao_b": id_talhao_b,
        "cultura_nome": f"Cultura {unique_suffix}",
        "safra_ano": date.today().year,
    }
