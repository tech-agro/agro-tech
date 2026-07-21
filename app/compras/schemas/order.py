from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.compras.enum import OrderStatus
from app.compras.schemas.order_item import OrderItemCreateSchema


class OrderCreateSchema(BaseModel):
    id_fornecedor: int
    data_pedido: date | None = None
    status: OrderStatus = OrderStatus.ABERTO
    itens: list[OrderItemCreateSchema] = Field(min_length=1)


class OrderUpdateSchema(BaseModel):
    id_fornecedor: int | None = None
    data_pedido: date | None = None
    status: OrderStatus | None = None


class OrderReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pedido: int
    id_fornecedor: int
    data_pedido: date | None
    status: OrderStatus
    fornecedor_nome: str | None = None
