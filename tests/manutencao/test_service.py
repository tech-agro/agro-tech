"""Testes de integracao do ManutencaoService."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.manutencao.schemas.manutencao import ManutencaoCreateSchema
from app.manutencao.schemas.manutencao_corretiva import ManutencaoCorretivaUpdateSchema
from app.manutencao.schemas.ordem_servico import OrdemServicoCreateSchema
from app.manutencao.service import (
    ManutencaoConflictError,
    ManutencaoValidationError,
)

pytestmark = pytest.mark.integration


def test_criar_manutencao_corretiva_marca_maquina_em_manutencao(
    manutencao_service,
    sample_maquina,
):
    result = manutencao_service.criar_manutencao_corretiva(
        ManutencaoCreateSchema(id_maquina=sample_maquina.id_maquina, status="ABERTA"),
        defeito_relatado="Superaquecimento do motor",
    )

    assert result.manutencao.tipo == "CORRETIVA"
    assert result.manutencao.status == "ABERTA"
    assert result.corretiva.defeito_relatado == "Superaquecimento do motor"

    maquina = manutencao_service.get_maquina(sample_maquina.id_maquina)
    assert maquina.status == "EM_MANUTENCAO"


def test_criar_manutencao_preventiva_exige_plano_da_mesma_maquina(
    manutencao_service,
    sample_maquina,
    sample_plano,
    db_engine,
    id_fazenda,
    id_tipo_maquina,
    unique_suffix,
):
    with db_engine.begin() as conn:
        outra_maquina = conn.execute(
            text(
                """
                INSERT INTO maquina (id_tipo_maquina, id_fazenda, nome, status)
                VALUES (:tipo, :fazenda, :nome, 'DISPONIVEL')
                RETURNING id_maquina
                """
            ),
            {
                "tipo": id_tipo_maquina,
                "fazenda": id_fazenda,
                "nome": f"Outra {unique_suffix}",
            },
        ).scalar_one()

    with pytest.raises(ManutencaoValidationError):
        manutencao_service.criar_manutencao_preventiva(
            ManutencaoCreateSchema(
                id_maquina=outra_maquina,
                status="ABERTA",
            ),
            id_plano=sample_plano,
        )

    result = manutencao_service.criar_manutencao_preventiva(
        ManutencaoCreateSchema(
            id_maquina=sample_maquina.id_maquina,
            status="ABERTA",
        ),
        id_plano=sample_plano,
        hodometro_execucao=1500.0,
    )
    assert result.manutencao.tipo == "PREVENTIVA"
    assert result.preventiva.id_plano == sample_plano


def test_nao_permite_duas_manutencoes_abertas_na_mesma_maquina(
    manutencao_service,
    sample_maquina,
):
    manutencao_service.criar_manutencao_corretiva(
        ManutencaoCreateSchema(id_maquina=sample_maquina.id_maquina, status="ABERTA"),
        defeito_relatado="Falha eletrica",
    )

    with pytest.raises(ManutencaoConflictError):
        manutencao_service.criar_manutencao_corretiva(
            ManutencaoCreateSchema(
                id_maquina=sample_maquina.id_maquina,
                status="ABERTA",
            ),
            defeito_relatado="Nova falha",
        )


def test_concluir_manutencao_corretiva_exige_solucao(
    manutencao_service,
    sample_maquina,
):
    result = manutencao_service.criar_manutencao_corretiva(
        ManutencaoCreateSchema(id_maquina=sample_maquina.id_maquina, status="ABERTA"),
        defeito_relatado="Correia danificada",
    )
    id_manutencao = result.manutencao.id_manutencao
    manutencao_service.iniciar_manutencao(id_manutencao)

    with pytest.raises(ManutencaoValidationError):
        manutencao_service.concluir_manutencao(id_manutencao, custo=250.0)

    manutencao_service.atualizar_manutencao_corretiva(
        id_manutencao,
        ManutencaoCorretivaUpdateSchema(solucao_aplicada="Correia substituida"),
    )
    concluida = manutencao_service.concluir_manutencao(id_manutencao, custo=250.0)

    assert concluida.status == "CONCLUIDA"
    assert concluida.custo == 250.0
    assert manutencao_service.get_maquina(sample_maquina.id_maquina).status == "DISPONIVEL"


def test_concluir_manutencao_registra_historico_e_conta_pagar(
    manutencao_service,
    db_engine,
    sample_maquina,
):
    result = manutencao_service.criar_manutencao_corretiva(
        ManutencaoCreateSchema(id_maquina=sample_maquina.id_maquina, status="ABERTA"),
        defeito_relatado="Vazamento hidraulico",
    )
    id_manutencao = result.manutencao.id_manutencao
    manutencao_service.iniciar_manutencao(id_manutencao)
    manutencao_service.atualizar_manutencao_corretiva(
        id_manutencao,
        ManutencaoCorretivaUpdateSchema(solucao_aplicada="Retentor trocado"),
    )
    manutencao_service.concluir_manutencao(id_manutencao, custo=480.0)

    with db_engine.connect() as conn:
        historico = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM historico_manutencao
                WHERE id_manutencao = :id_manutencao
                """
            ),
            {"id_manutencao": id_manutencao},
        ).scalar_one()
        conta = conn.execute(
            text(
                """
                SELECT valor, status::text
                FROM conta_pagar
                WHERE id_manutencao = :id_manutencao
                """
            ),
            {"id_manutencao": id_manutencao},
        ).one()

    assert historico == 1
    assert float(conta.valor) == 480.0
    assert conta.status == "ABERTA"


def test_concluir_manutencao_preventiva_recalcula_plano(
    manutencao_service,
    manutencao_repository,
    db_engine,
    sample_maquina,
    sample_plano,
):
    result = manutencao_service.criar_manutencao_preventiva(
        ManutencaoCreateSchema(
            id_maquina=sample_maquina.id_maquina,
            status="ABERTA",
        ),
        id_plano=sample_plano,
        hodometro_execucao=1000.0,
    )
    id_manutencao = result.manutencao.id_manutencao
    manutencao_service.iniciar_manutencao(id_manutencao)

    dt_fim = date.today()
    manutencao_service.concluir_manutencao(id_manutencao, custo=120.0, dt_fim=dt_fim)

    plano = manutencao_repository.get_plano_by_id(sample_plano)
    assert plano is not None
    assert plano.proxima_execucao == dt_fim + timedelta(days=90)

    with db_engine.connect() as conn:
        conta = conn.execute(
            text(
                """
                SELECT valor, vencimento
                FROM conta_pagar
                WHERE id_manutencao = :id_manutencao
                """
            ),
            {"id_manutencao": id_manutencao},
        ).one()
    assert float(conta.valor) == 120.0
    assert conta.vencimento == dt_fim


def test_cancelar_manutencao_restaura_disponibilidade(
    manutencao_service,
    sample_maquina,
):
    result = manutencao_service.criar_manutencao_corretiva(
        ManutencaoCreateSchema(id_maquina=sample_maquina.id_maquina, status="ABERTA"),
        defeito_relatado="Alarme no painel",
    )
    id_manutencao = result.manutencao.id_manutencao
    assert manutencao_service.get_maquina(sample_maquina.id_maquina).status == "EM_MANUTENCAO"

    cancelada = manutencao_service.cancelar_manutencao(id_manutencao)
    assert cancelada.status == "CANCELADA"
    assert manutencao_service.get_maquina(sample_maquina.id_maquina).status == "DISPONIVEL"


def test_concluir_ordem_servico(manutencao_service, manutencao_aberta):
    ordem = manutencao_service.create_ordem_servico(
        OrdemServicoCreateSchema(
            id_manutencao=manutencao_aberta,
            descricao="Execucao completa do servico",
            status="EM_EXECUCAO",
        )
    )

    concluida = manutencao_service.concluir_ordem_servico(ordem.id_ordem_servico)
    assert concluida.status == "CONCLUIDA"


def test_nao_abre_ordem_servico_para_manutencao_encerrada(
    manutencao_service,
    sample_maquina,
):
    result = manutencao_service.criar_manutencao_corretiva(
        ManutencaoCreateSchema(id_maquina=sample_maquina.id_maquina, status="ABERTA"),
        defeito_relatado="Sensor com falha",
    )
    id_manutencao = result.manutencao.id_manutencao
    manutencao_service.cancelar_manutencao(id_manutencao)

    with pytest.raises(ManutencaoConflictError):
        manutencao_service.create_ordem_servico(
            OrdemServicoCreateSchema(
                id_manutencao=id_manutencao,
                descricao="Tentativa invalida",
                status="ABERTA",
            )
        )
