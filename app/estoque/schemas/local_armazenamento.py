"""Schemas Pydantic da entidade local_armazenamento."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LocalArmazenamentoCreateSchema(BaseModel):
    descricao: str = Field(min_length=1, max_length=255)
    capacidade: Decimal | None = Field(default=None, gt=0)


class LocalArmazenamentoUpdateSchema(BaseModel):
    descricao: str | None = Field(default=None, min_length=1, max_length=255)
    capacidade: Decimal | None = Field(default=None, gt=0)


class LocalArmazenamentoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_local: int
    descricao: str
    capacidade: Decimal | None