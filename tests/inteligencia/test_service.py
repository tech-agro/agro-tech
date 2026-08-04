"""Testes de integracao do InteligenciaService."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.inteligencia.errors import (
    InteligenciaConflictError,
    InteligenciaNotFoundError,
    InteligenciaValidationError,
)
from app.inteligencia.repository import MedicaoIndicadorFilters
from app.inteligencia.schemas import (
    IndicadorCreateSchema,
    MedicaoIndicadorCreateSchema,
    MedicaoIndicadorUpdateSchema,
)

pytestmark = pytest.mark.integration


def test_criar_indicador_rejeita_nome_duplicado(inteligencia_service, unique_suffix):
    nome = f"Indicador Unico {unique_suffix}"
    inteligencia_service.criar_indicador(IndicadorCreateSchema(nome=nome))

    with pytest.raises(InteligenciaConflictError):
        inteligencia_service.criar_indicador(IndicadorCreateSchema(nome=nome))


def test_excluir_indicador_com_medicoes_bloqueado(
    inteligencia_service,
    sample_indicador,
    id_safra,
):
    inteligencia_service.registrar_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("1.00"),
            data_referencia=date.today(),
        )
    )

    with pytest.raises(InteligenciaConflictError):
        inteligencia_service.excluir_indicador(sample_indicador.id_indicador)


def test_registrar_medicao_exige_valor(inteligencia_service, sample_indicador, id_safra):
    with pytest.raises(InteligenciaValidationError):
        inteligencia_service.registrar_medicao(
            MedicaoIndicadorCreateSchema(
                id_indicador=sample_indicador.id_indicador,
                id_safra=id_safra,
                valor=None,
            )
        )


def test_registrar_medicao_rejeita_duplicata(
    inteligencia_service,
    sample_indicador,
    id_safra,
):
    hoje = date.today()
    payload = MedicaoIndicadorCreateSchema(
        id_indicador=sample_indicador.id_indicador,
        id_safra=id_safra,
        valor=Decimal("15.00"),
        data_referencia=hoje,
    )
    inteligencia_service.registrar_medicao(payload)

    with pytest.raises(InteligenciaConflictError):
        inteligencia_service.registrar_medicao(payload)


def test_registrar_medicao_rejeita_data_futura(
    inteligencia_service,
    sample_indicador,
    id_safra,
):
    with pytest.raises(InteligenciaValidationError):
        inteligencia_service.registrar_medicao(
            MedicaoIndicadorCreateSchema(
                id_indicador=sample_indicador.id_indicador,
                id_safra=id_safra,
                valor=Decimal("10.00"),
                data_referencia=date.today() + timedelta(days=1),
            )
        )


def test_registrar_medicao_rejeita_safra_inexistente(
    inteligencia_service,
    sample_indicador,
):
    with pytest.raises(InteligenciaNotFoundError):
        inteligencia_service.registrar_medicao(
            MedicaoIndicadorCreateSchema(
                id_indicador=sample_indicador.id_indicador,
                id_safra=999_999,
                valor=Decimal("10.00"),
                data_referencia=date.today(),
            )
        )


def test_agregar_medicoes_calcula_media(
    inteligencia_service,
    sample_indicador,
    id_safra,
):
    inteligencia_service.registrar_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("20.00"),
            data_referencia=date.today(),
        )
    )
    inteligencia_service.registrar_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("40.00"),
            data_referencia=date.today() - timedelta(days=1),
        )
    )

    agregacao = inteligencia_service.agregar_medicoes(
        sample_indicador.id_indicador,
        id_safra=id_safra,
    )

    assert agregacao.total_medicoes == 2
    assert agregacao.valor_medio == Decimal("30.00")
    assert agregacao.valor_soma == Decimal("60.00")


def test_agregar_medicoes_periodo_invalido(inteligencia_service, sample_indicador):
    with pytest.raises(InteligenciaValidationError):
        inteligencia_service.agregar_medicoes(
            sample_indicador.id_indicador,
            data_inicio=date.today(),
            data_fim=date.today() - timedelta(days=1),
        )


def test_listar_medicoes_com_filtro(inteligencia_service, sample_indicador, id_safra):
    inteligencia_service.registrar_medicao(
        MedicaoIndicadorCreateSchema(
            id_indicador=sample_indicador.id_indicador,
            id_safra=id_safra,
            valor=Decimal("5.00"),
            data_referencia=date.today(),
        )
    )

    medicoes = inteligencia_service.listar_medicoes(
        MedicaoIndicadorFilters(id_indicador=sample_indicador.id_indicador)
    )

    assert len(medicoes) == 1
    assert medicoes[0].valor == Decimal("5.00")


def test_atualizar_medicao(inteligencia_service, sample_medicao):
    atualizada = inteligencia_service.atualizar_medicao(
        sample_medicao["id_medicao"],
        MedicaoIndicadorUpdateSchema(valor=Decimal("77.77")),
    )

    assert atualizada.valor == Decimal("77.77")
