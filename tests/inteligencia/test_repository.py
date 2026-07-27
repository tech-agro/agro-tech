"""Testes de integracao do InteligenciaRepository."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.inteligencia.repository import IndicadorFilters, MedicaoIndicadorFilters
from app.inteligencia.schemas import (
    IndicadorCreateSchema,
    IndicadorUpdateSchema,
    MedicaoIndicadorCreateSchema,
    MedicaoIndicadorUpdateSchema,
)

pytestmark = pytest.mark.integration


def test_create_and_get_indicador(indicador_repository, unique_suffix):
    criado = indicador_repository.create_indicador(
        IndicadorCreateSchema(nome=f"Custo {unique_suffix}", unidade="R$")
    )

    encontrado = indicador_repository.get_indicador(criado.id_indicador)

    assert encontrado is not None
    assert encontrado.nome == f"Custo {unique_suffix}"
    assert encontrado.unidade == "R$"


def test_list_indicadores_with_filters(indicador_repository, unique_suffix):
    indicador_repository.create_indicador(
        IndicadorCreateSchema(nome=f"Eficiencia {unique_suffix}", unidade="%")
    )
    indicador_repository.create_indicador(
        IndicadorCreateSchema(nome=f"Outro {unique_suffix}", unidade="R$")
    )

    por_nome = indicador_repository.list_indicadores(
        IndicadorFilters(nome="Eficiencia")
    )
    por_unidade = indicador_repository.list_indicadores(IndicadorFilters(unidade="R$"))

    assert len(por_nome) == 1
    assert por_nome[0].nome.startswith("Eficiencia")
    assert len(por_unidade) == 1
    assert por_unidade[0].unidade == "R$"


def test_update_indicador(indicador_repository, sample_indicador):
    atualizado = indicador_repository.update_indicador(
        sample_indicador.id_indicador,
        IndicadorUpdateSchema(nome="Produtividade Atualizada", unidade="t/ha"),
    )

    assert atualizado is not None
    assert atualizado.nome == "Produtividade Atualizada"
    assert atualizado.unidade == "t/ha"


def test_delete_indicador(indicador_repository, unique_suffix):
    criado = indicador_repository.create_indicador(
        IndicadorCreateSchema(nome=f"Temp {unique_suffix}")
    )

    assert indicador_repository.delete_indicador(criado.id_indicador) is True
    assert indicador_repository.get_indicador(criado.id_indicador) is None


def test_get_by_nome_case_insensitive(indicador_repository, unique_suffix):
    nome = f"MTBF {unique_suffix}"
    indicador_repository.create_indicador(IndicadorCreateSchema(nome=nome))

    encontrado = indicador_repository.get_by_nome(nome.upper())

    assert encontrado is not None
    assert encontrado.nome == nome


def test_create_and_get_medicao(
    medicao_repository,
    sample_indicador,
    id_safra,
):
    criada = medicao_repository.create_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("250.00"),
            data_referencia=date.today(),
        )
    )

    encontrada = medicao_repository.get_medicao(criada.id_medicao)

    assert encontrada is not None
    assert encontrada.valor == Decimal("250.00")
    assert encontrada.indicador_nome == sample_indicador.nome


def test_list_medicoes_by_indicador(
    medicao_repository,
    sample_indicador,
    id_safra,
):
    medicao_repository.create_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("10.00"),
            data_referencia=date.today(),
        )
    )
    medicao_repository.create_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("20.00"),
            data_referencia=date.today() - timedelta(days=1),
        )
    )

    medicoes = medicao_repository.list_medicoes(
        MedicaoIndicadorFilters(id_indicador=sample_indicador.id_indicador)
    )

    assert len(medicoes) == 2


def test_update_and_delete_medicao(medicao_repository, sample_medicao):
    id_medicao = sample_medicao["id_medicao"]

    atualizada = medicao_repository.update_medicao(
        id_medicao,
        MedicaoIndicadorUpdateSchema(valor=Decimal("999.99")),
    )

    assert atualizada is not None
    assert atualizada.valor == Decimal("999.99")

    assert medicao_repository.delete_medicao(id_medicao) is True
    assert medicao_repository.get_medicao(id_medicao) is None


def test_agregar_medicoes(medicao_repository, sample_indicador, id_safra):
    medicao_repository.create_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("10.00"),
            data_referencia=date.today(),
        )
    )
    medicao_repository.create_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("30.00"),
            data_referencia=date.today() - timedelta(days=1),
        )
    )

    agregacao = medicao_repository.agregar_medicoes(
        id_indicador=sample_indicador.id_indicador,
        id_safra=id_safra,
    )

    assert agregacao.total_medicoes == 2
    assert agregacao.valor_soma == Decimal("40.00")
    assert agregacao.valor_medio == Decimal("20.00")
    assert agregacao.valor_minimo == Decimal("10.00")
    assert agregacao.valor_maximo == Decimal("30.00")
