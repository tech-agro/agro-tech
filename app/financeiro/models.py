"""Modelos (Pydantic) do domínio financeiro."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.financeiro.enum import StatusContaReceber


class ContaReceberModel(BaseModel):
    id_conta_receber: int
    id_venda: int
    valor: Decimal
    vencimento: date | None = None
    status: StatusContaReceber
