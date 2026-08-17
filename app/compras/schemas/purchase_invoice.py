from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PurchaseInvoiceCreateSchema(BaseModel):
    numero: str = Field(min_length=1, max_length=30)
    serie: str = Field(min_length=1, max_length=10)
    data_emissao: date
    valor_total: float = Field(gt=0)
    chave_acesso: str | None = Field(default=None, max_length=44)


class PurchaseInvoiceUpdateSchema(BaseModel):
    numero: str | None = Field(default=None, min_length=1, max_length=30)
    serie: str | None = Field(default=None, min_length=1, max_length=10)
    data_emissao: date | None = None
    valor_total: float | None = Field(default=None, gt=0)
    chave_acesso: str | None = Field(default=None, max_length=44)


class PurchaseInvoiceReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_nota_fiscal: int
    id_pedido: int
    id_fornecedor: int
    numero: str
    serie: str
    data_emissao: date
    valor_total: float
    chave_acesso: str | None = None
