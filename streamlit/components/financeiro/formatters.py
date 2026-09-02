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
    AplicacaoOptionSchema,
)


def compra_label(option: CompraOptionSchema) -> str:
    return option.label


def manutencao_label(option: ManutencaoOptionSchema) -> str:
    return option.label


def despesa_logistica_label(
    option: DespesaLogisticaOptionSchema,
) -> str:
    return option.label


def aplicacao_label(option: AplicacaoOptionSchema) -> str:
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


STATUS_CONTA_LABELS: dict[str, str] = {
    "ABERTA": "Aberta",
    "PARCIALMENTE_PAGA": "Parcial",
    "PARCIALMENTE_RECEBIDA": "Parcial",
    "PAGA": "Paga",
    "RECEBIDA": "Recebida",
    "VENCIDA": "Vencida",
    "CANCELADA": "Cancelada",
}

STATUS_CONTA_OPTIONS: list[str] = ["Aberta", "Parcial", "Paga", "Recebida", "Vencida", "Cancelada", "—"]

STATUS_CONTA_TONE: dict[str, str] = {
    "Aberta": "blue",
    "Parcial": "orange",
    "Paga": "green",
    "Recebida": "green",
    "Vencida": "red",
    "Cancelada": "gray",
    "—": "gray",
}


def status_conta_label(status) -> str:
    raw = status.value if status is not None and hasattr(status, "value") else status
    if not raw:
        return "—"
    return STATUS_CONTA_LABELS.get(raw, str(raw).title())