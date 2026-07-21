"""Read-only options for purchases UI until catalog modules own these APIs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.comercial.enum import UnitSymbol


class ProductOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_produto: int
    nome: str
    unidade_sigla: UnitSymbol
    unidade_descricao: str


class SupplierOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_fornecedor: int
    nome: str
    categoria: str | None = None


class CostCenterOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_centro_custo: int
    nome: str
