"""Schemas Pydantic da entidade lote."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.estoque.enum import LotOriginType, StatusLote


class LoteCreateSchema(BaseModel):
    id_colheita: int | None = None
    id_produto: int
    validade: date | None = None
    qualidade: str | None = Field(default=None, max_length=80)
    status: StatusLote = StatusLote.LIBERADO
    tipo_origem: LotOriginType = LotOriginType.COMPRA
    quantidade_inicial: Decimal | None = None


class LoteUpdateSchema(BaseModel):
    validade: date | None = None
    qualidade: str | None = Field(default=None, max_length=80)
    status: StatusLote | None = None


class LoteReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_lote: int
    id_colheita: int | None
    id_produto: int
    codigo_lote: str
    validade: date | None
    qualidade: str | None
    status: StatusLote
    tipo_origem: LotOriginType | None = None
    quantidade_inicial: Decimal | None = None
    produto_nome: str | None = None


class LocalizacaoLoteSchema(BaseModel):
    id_lote: int
    codigo_lote: str
    produto_nome: str | None
    local_descricao: str
    quantidade_atual: Decimal
    quantidade_reservada: Decimal
