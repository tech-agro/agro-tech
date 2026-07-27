"""Schemas Pydantic do módulo financeiro."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.financeiro.enum import (
    StatusContaPagarEnum,
    StatusContaReceberEnum,
)


# ============================================================
# CONTAS A PAGAR
# ============================================================

class ContaPagarCreateSchema(BaseModel):
    id_compra: int | None = None
    id_manutencao: int | None = None
    id_despesa_logistica: int | None = None
    id_aplicacao: int | None = None
    valor: Decimal = Field(ge=0)
    vencimento: date | None = None

    @model_validator(mode="after")
    def validar_origem(self):
        origens = [
            self.id_compra,
            self.id_manutencao,
            self.id_despesa_logistica,
            self.id_aplicacao,
        ]

        if sum(origem is not None for origem in origens) != 1:
            raise ValueError(
                "Conta a pagar deve possuir exatamente uma origem."
            )

        return self


class ContaPagarUpdateSchema(BaseModel):
    vencimento: date | None = None
    status: StatusContaPagarEnum | None = None


class ContaPagarReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_conta_pagar: int
    id_compra: int | None
    id_manutencao: int | None
    id_despesa_logistica: int | None
    id_aplicacao: int | None = None
    valor: Decimal
    vencimento: date | None
    status: StatusContaPagarEnum

    origem: str | None = None

    compra_valor: Decimal | None = None

    manutencao_tipo: str | None = None
    manutencao_custo: Decimal | None = None
    manutencao_data: date | None = None

    despesa_descricao: str | None = None
    despesa_tipo: str | None = None
    despesa_data: date | None = None

    valor_pago: Decimal = Decimal("0.00")
    saldo: Decimal = Decimal("0.00")


# ============================================================
# PAGAMENTOS
# ============================================================

class PagamentoCreateSchema(BaseModel):
    id_conta_pagar: int
    valor_pago: Decimal = Field(ge=0)
    data_pagamento: date | None = None
    forma_pagamento: str | None = Field(default=None, max_length=80)


class PagamentoUpdateSchema(BaseModel):
    data_pagamento: date | None = None
    forma_pagamento: str | None = Field(default=None, max_length=80)


class PagamentoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pagamento: int
    id_conta_pagar: int
    valor_pago: Decimal
    data_pagamento: date | None
    forma_pagamento: str | None

    vencimento: date | None = None
    status: StatusContaPagarEnum | None = None
    saldo: Decimal | None = None


# ============================================================
# CONTAS A RECEBER
# ============================================================

class ContaReceberCreateSchema(BaseModel):
    id_venda: int
    valor: Decimal = Field(ge=0)
    vencimento: date | None = None


class ContaReceberUpdateSchema(BaseModel):
    vencimento: date | None = None
    status: StatusContaReceberEnum | None = None


class ContaReceberReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_conta_receber: int
    id_venda: int
    valor: Decimal
    vencimento: date | None
    status: StatusContaReceberEnum

    valor_venda: Decimal | None = None
    data_venda: date | None = None

    valor_recebido: Decimal = Decimal("0.00")
    saldo: Decimal = Decimal("0.00")


# ============================================================
# RECEBIMENTOS
# ============================================================

class RecebimentoCreateSchema(BaseModel):
    id_conta_receber: int
    valor_recebido: Decimal = Field(ge=0)
    data_recebimento: date | None = None
    forma_pagamento: str | None = Field(default=None, max_length=80)


class RecebimentoUpdateSchema(BaseModel):
    data_recebimento: date | None = None
    forma_pagamento: str | None = Field(default=None, max_length=80)


class RecebimentoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_recebimento: int
    id_conta_receber: int
    valor_recebido: Decimal
    data_recebimento: date | None
    forma_pagamento: str | None

    vencimento: date | None = None
    status: StatusContaReceberEnum | None = None
    saldo: Decimal | None = None


# ============================================================
# CONFIGURAÇÃO FINANCEIRA
# ============================================================

class ConfiguracaoFinanceiraUpdateSchema(BaseModel):
    limite_aprovacao_automatica: Decimal = Field(ge=0)


class ConfiguracaoFinanceiraReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_configuracao: int
    limite_aprovacao_automatica: Decimal
    atualizado_em: datetime


class FluxoCaixaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_fluxo: int
    id_conta_pagar: int | None
    id_conta_receber: int | None
    id_pagamento: int | None = None
    id_recebimento: int | None = None

    valor: Decimal
    tipo: str | None
    data_movimento: date | None

    origem: str | None = None
    descricao_origem: str | None = None