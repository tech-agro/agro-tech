"""Schemas for saldo_lote."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SaldoLoteReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_saldo_lote: int
    id_estoque: int
    id_lote: int
    quantidade_atual: Decimal
    quantidade_reservada: Decimal
    lote_codigo: str | None = None
    produto_nome: str | None = None
