"""Schemas Pydantic da entidade saldo_estoque."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SaldoEstoqueReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_saldo: int
    id_estoque: int
    id_produto: int
    quantidade_atual: Decimal
    produto_nome: str | None = None