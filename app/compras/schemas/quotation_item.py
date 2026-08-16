from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QuotationItemCreateSchema(BaseModel):
    id_produto: int
    quantidade: float = Field(gt=0)
    preco_unitario: float = Field(ge=0)


class QuotationItemUpdateSchema(BaseModel):
    quantidade: float | None = Field(default=None, gt=0)
    preco_unitario: float | None = Field(default=None, ge=0)


class QuotationItemReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_item_cotacao: int
    id_cotacao: int
    id_produto: int
    quantidade: float
    preco_unitario: float
    produto_nome: str | None = None
