"""Testes de integracao do ManutencaoRepository."""

from __future__ import annotations

import pytest

from app.manutencao.repository import MaquinaFilters, OrdemServicoFilters
from app.manutencao.schemas.maquina import MaquinaCreateSchema, MaquinaUpdateSchema
from app.manutencao.schemas.ordem_servico import (
    OrdemServicoCreateSchema,
    OrdemServicoUpdateSchema,
)

pytestmark = pytest.mark.integration


def test_create_and_get_maquina(
    manutencao_repository,
    id_fazenda,
    id_tipo_maquina,
    unique_suffix,
):
    created = manutencao_repository.create_maquina(
        MaquinaCreateSchema(
            id_tipo_maquina=id_tipo_maquina,
            nome=f"Pulverizador {unique_suffix}",
            status="DISPONIVEL",
        ),
        id_fazenda=id_fazenda,
    )

    assert created is not None
    assert created.nome == f"Pulverizador {unique_suffix}"
    assert created.status == "DISPONIVEL"

    found = manutencao_repository.get_maquina_by_id(created.id_maquina)
    assert found == created


def test_list_maquinas_with_filters(manutencao_repository, sample_maquina, id_fazenda):
    by_status = manutencao_repository.list_maquinas(
        MaquinaFilters(status="DISPONIVEL")
    )
    assert any(m.id_maquina == sample_maquina.id_maquina for m in by_status)

    by_fazenda = manutencao_repository.list_maquinas(
        MaquinaFilters(id_fazenda=id_fazenda)
    )
    assert len(by_fazenda) >= 1

    by_nome = manutencao_repository.list_maquinas(
        MaquinaFilters(nome=sample_maquina.nome[:6])
    )
    assert any(m.id_maquina == sample_maquina.id_maquina for m in by_nome)


def test_update_maquina(manutencao_repository, sample_maquina):
    updated = manutencao_repository.update_maquina(
        sample_maquina.id_maquina,
        MaquinaUpdateSchema(nome="Trator Atualizado", status="EM_USO"),
    )

    assert updated is not None
    assert updated.nome == "Trator Atualizado"
    assert updated.status == "EM_USO"


def test_delete_maquina(manutencao_repository, sample_maquina):
    deleted = manutencao_repository.delete_maquina(sample_maquina.id_maquina)
    assert deleted is True
    assert manutencao_repository.get_maquina_by_id(sample_maquina.id_maquina) is None


def test_create_and_get_ordem_servico(manutencao_repository, manutencao_aberta):
    created = manutencao_repository.create_ordem_servico(
        OrdemServicoCreateSchema(
            id_manutencao=manutencao_aberta,
            descricao="Trocar filtro de oleo",
            status="ABERTA",
        )
    )

    assert created is not None
    assert created.id_manutencao == manutencao_aberta
    assert created.descricao == "Trocar filtro de oleo"

    found = manutencao_repository.get_ordem_servico_by_id(created.id_ordem_servico)
    assert found == created


def test_list_ordens_servico_by_manutencao(manutencao_repository, manutencao_aberta):
    ordem = manutencao_repository.create_ordem_servico(
        OrdemServicoCreateSchema(
            id_manutencao=manutencao_aberta,
            descricao="Inspecionar sistema hidraulico",
            status="EM_EXECUCAO",
        )
    )
    assert ordem is not None

    ordens = manutencao_repository.list_ordens_servico(
        OrdemServicoFilters(id_manutencao=manutencao_aberta)
    )
    assert len(ordens) == 1
    assert ordens[0].id_ordem_servico == ordem.id_ordem_servico


def test_update_and_delete_ordem_servico(manutencao_repository, manutencao_aberta):
    ordem = manutencao_repository.create_ordem_servico(
        OrdemServicoCreateSchema(
            id_manutencao=manutencao_aberta,
            descricao="Servico inicial",
            status="ABERTA",
        )
    )
    assert ordem is not None

    updated = manutencao_repository.update_ordem_servico(
        ordem.id_ordem_servico,
        OrdemServicoUpdateSchema(
            descricao="Servico revisado",
            status="EM_EXECUCAO",
        ),
    )
    assert updated is not None
    assert updated.descricao == "Servico revisado"
    assert updated.status == "EM_EXECUCAO"

    deleted = manutencao_repository.delete_ordem_servico(ordem.id_ordem_servico)
    assert deleted is True
    assert (
        manutencao_repository.get_ordem_servico_by_id(ordem.id_ordem_servico) is None
    )
