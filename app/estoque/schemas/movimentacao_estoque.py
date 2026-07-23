"""Schemas Pydantic da entidade movimentacao_estoque."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MovimentacaoEstoqueReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_movimentacao: int
    id_estoque: int
    id_produto: int
    id_lote: int | None
    tipo_movimentacao: str
    quantidade: Decimal
    data_movimentacao: datetime
    produto_nome: str | None = None
    lote_codigo: str | None = None