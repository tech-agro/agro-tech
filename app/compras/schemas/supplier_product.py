from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SupplierProductCreateSchema(BaseModel):
    id_fornecedor: int
    id_produto: int
    preco_referencia: float | None = Field(default=None, ge=0)
    prazo_entrega_dias: int | None = None


class SupplierProductUpdateSchema(BaseModel):
    preco_referencia: float | None = Field(default=None, ge=0)
    prazo_entrega_dias: int | None = None


class SupplierProductReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_fornecedor: int
    id_produto: int
    preco_referencia: float | None
    prazo_entrega_dias: int | None
