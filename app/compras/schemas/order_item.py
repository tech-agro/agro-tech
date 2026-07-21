from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.comercial.enum import UnitSymbol


class OrderItemCreateSchema(BaseModel):
    """Nested POST body; order id comes from the URL."""

    id_produto: int
    quantidade: float = Field(gt=0)
    valor_unitario: float = Field(ge=0)


class OrderItemUpdateSchema(BaseModel):
    quantidade: float | None = Field(default=None, gt=0)
    valor_unitario: float | None = Field(default=None, ge=0)


class OrderItemReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_item: int
    id_pedido: int
    id_produto: int
    quantidade: float
    valor_unitario: float
    produto_nome: str | None = None
    unidade_sigla: UnitSymbol | None = None
