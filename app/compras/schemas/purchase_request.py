from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.compras.enum import PurchaseRequestStatus, PurchaseType
from app.compras.schemas.purchase_request_item import PurchaseRequestItemCreateSchema


class PurchaseRequestCreateSchema(BaseModel):
    data_solicitacao: date | None = None
    status: PurchaseRequestStatus = PurchaseRequestStatus.RASCUNHO
    tipo_compra: PurchaseType = PurchaseType.INSUMO
    observacao: str | None = None
    id_tipo_maquina: int | None = None
    patrimonio: str | None = None
    id_fazenda: int | None = None
    itens: list[PurchaseRequestItemCreateSchema] = Field(min_length=1)


class PurchaseRequestUpdateSchema(BaseModel):
    data_solicitacao: date | None = None
    status: PurchaseRequestStatus | None = None
    tipo_compra: PurchaseType | None = None
    observacao: str | None = None
    id_tipo_maquina: int | None = None
    patrimonio: str | None = None
    id_fazenda: int | None = None


class PurchaseRequestReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_solicitacao: int
    data_solicitacao: date
    status: PurchaseRequestStatus
    tipo_compra: PurchaseType
    observacao: str | None = None
    id_tipo_maquina: int | None = None
    patrimonio: str | None = None
    id_fazenda: int | None = None
    id_pedido: int | None = None


class ConvertRequestToOrderSchema(BaseModel):
    id_fornecedor: int
    item_prices: dict[int, float] = Field(
        description="Map of request item id (id_item) to unit price"
    )
