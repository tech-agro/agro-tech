from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PurchaseCreateSchema(BaseModel):
    id_pedido: int
    id_centro_custo: int
    valor_total: float = Field(ge=0)
    data_compra: date | None = None


class PurchaseUpdateSchema(BaseModel):
    valor_total: float | None = Field(default=None, ge=0)
    data_compra: date | None = None


class PurchaseReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_compra: int
    id_pedido: int
    id_centro_custo: int
    valor_total: float
    data_compra: date | None
