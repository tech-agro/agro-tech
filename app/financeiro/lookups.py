"""Schemas Pydantic para lookups do módulo financeiro."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.financeiro.enum import (
    StatusContaPagarEnum,
    StatusContaReceberEnum,
)


class CompraOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_compra: int
    label: str
    valor_total: Decimal | None = None


class ManutencaoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_manutencao: int
    label: str
    tipo: str | None = None
    custo: Decimal | None = None


class DespesaLogisticaOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_despesa: int
    label: str
    descricao: str
    valor: Decimal


class VendaOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_venda: int
    label: str
    valor_total: Decimal
    data_venda: date | None = None


class ContaPagarOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_conta_pagar: int
    label: str
    valor: Decimal
    saldo: Decimal
    vencimento: date | None = None
    status: StatusContaPagarEnum


class ContaReceberOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_conta_receber: int
    label: str
    valor: Decimal
    saldo: Decimal
    vencimento: date | None = None
    status: StatusContaReceberEnum


class FormaPagamentoOptionSchema(BaseModel):
    valor: str