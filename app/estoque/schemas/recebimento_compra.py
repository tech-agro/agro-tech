"""Schemas Pydantic da entidade recebimento_compra."""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RecebimentoCompraCreateSchema(BaseModel):
    id_item_pedido: int
    id_estoque: int
    quantidade_recebida: Decimal = Field(gt=0)
    data_recebimento: datetime | None = None
    codigo_lote: str | None = Field(default=None, min_length=1, max_length=120)
    validade_lote: date | None = None


class RecebimentoCompraReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_recebimento: int
    id_item_pedido: int
    id_estoque: int
    id_movimentacao: int
    quantidade_recebida: Decimal
    data_recebimento: datetime