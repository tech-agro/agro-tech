"""Schemas for supplier CRUD in the purchases domain."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SupplierCreateSchema(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    documento: str = Field(min_length=1, max_length=50)
    categoria: str | None = Field(default=None, max_length=100)


class SupplierUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    documento: str | None = Field(default=None, min_length=1, max_length=50)
    categoria: str | None = Field(default=None, max_length=100)


class SupplierReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_fornecedor: int
    id_pessoa: int
    nome: str
    documento: str
    categoria: str | None = None
