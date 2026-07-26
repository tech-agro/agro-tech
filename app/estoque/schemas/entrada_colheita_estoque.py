"""Schemas Pydantic da entidade entrada_colheita_estoque."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class EntradaColheitaCreateSchema(BaseModel):
    id_colheita: int
    id_produto: int
    id_estoque: int
    quantidade: Decimal = Field(gt=0)
    codigo_lote: str = Field(min_length=1, max_length=120)
    validade_lote: date | None = None
    qualidade_lote: str | None = Field(default=None, max_length=80)
    data_entrada: datetime | None = None


class EntradaColheitaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_entrada_colheita: int
    id_colheita: int
    id_movimentacao: int