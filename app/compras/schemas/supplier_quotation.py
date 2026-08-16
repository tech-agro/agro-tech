from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.compras.enum import QuotationStatus
from app.compras.schemas.quotation_item import QuotationItemCreateSchema


class SupplierQuotationCreateSchema(BaseModel):
    id_fornecedor: int
    status: QuotationStatus = QuotationStatus.RASCUNHO
    prazo_entrega_dias: int | None = Field(default=None, ge=0)
    observacao: str | None = None
    itens: list[QuotationItemCreateSchema] = Field(min_length=1)


class SupplierQuotationUpdateSchema(BaseModel):
    status: QuotationStatus | None = None
    prazo_entrega_dias: int | None = Field(default=None, ge=0)
    observacao: str | None = None


class SupplierQuotationReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cotacao: int
    id_solicitacao: int
    id_fornecedor: int
    status: QuotationStatus
    prazo_entrega_dias: int | None = None
    observacao: str | None = None
    fornecedor_nome: str | None = None


class QuotationComparisonSchema(BaseModel):
    """Side-by-side comparison payload for the UI."""

    id_solicitacao: int
    produtos: list[dict]
    cotacoes: list[SupplierQuotationReadSchema]
