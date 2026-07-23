"""Schemas Pydantic da entidade estoque."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EstoqueCreateSchema(BaseModel):
    id_local: int


class EstoqueReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_estoque: int
    id_local: int
    local_descricao: str | None = None