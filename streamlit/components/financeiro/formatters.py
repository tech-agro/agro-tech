"""Funções auxiliares para exibição de rótulos no módulo financeiro."""

from __future__ import annotations

from components.shared.formatters import format_money

from app.financeiro.lookups import (
    CompraOptionSchema,
    ContaPagarOptionSchema,
    ContaReceberOptionSchema,
    DespesaLogisticaOptionSchema,
    FormaPagamentoOptionSchema,
    ManutencaoOptionSchema,
    VendaOptionSchema,
)


def compra_label(option: CompraOptionSchema) -> str:
    return option.label


def manutencao_label(option: ManutencaoOptionSchema) -> str:
    return option.label


def despesa_logistica_label(
    option: DespesaLogisticaOptionSchema,
) -> str:
    return option.label


def venda_label(option: VendaOptionSchema) -> str:
    return option.label


def conta_pagar_label(
    option: ContaPagarOptionSchema,
) -> str:
    return (
        f"{option.label} • "
        f"Saldo: {format_money(float(option.saldo))}"
    )


def conta_receber_label(
    option: ContaReceberOptionSchema,
) -> str:
    return (
        f"{option.label} • "
        f"Saldo: {format_money(float(option.saldo))}"
    )


def forma_pagamento_label(
    option: FormaPagamentoOptionSchema,
) -> str:
    return option.valor