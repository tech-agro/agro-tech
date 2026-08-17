from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PurchaseRequestItemCreateSchema(BaseModel):
    id_produto: int
    quantidade: float = Field(gt=0)


class PurchaseRequestItemUpdateSchema(BaseModel):
    id_produto: int | None = None
    quantidade: float | None = Field(default=None, gt=0)


class PurchaseRequestItemReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_item: int
    id_solicitacao: int
    id_produto: int
    quantidade: float
    produto_nome: str | None = None
    unidade_sigla: str | None = None
