"""Schemas Pydantic da entidade lote."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class LoteCreateSchema(BaseModel):
    id_colheita: int
    id_produto: int
    codigo_lote: str = Field(min_length=1, max_length=120)
    validade: date | None = None
    qualidade: str | None = Field(default=None, max_length=80)


class LoteUpdateSchema(BaseModel):
    validade: date | None = None
    qualidade: str | None = Field(default=None, max_length=80)


class LoteReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_lote: int
    id_colheita: int
    id_produto: int
    codigo_lote: str
    validade: date | None
    qualidade: str | None
    produto_nome: str | None = None