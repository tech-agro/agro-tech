from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoadCreateSchema(BaseModel):
    """Nested POST body; operation id comes from the URL."""

    id_lote: int
    id_item_venda: int | None = None
    quantidade: float | None = Field(default=None, gt=0)
    peso_previsto: float | None = Field(default=None, ge=0)


class LoadUpdateSchema(BaseModel):
    id_lote: int | None = None
    id_item_venda: int | None = None
    quantidade: float | None = Field(default=None, gt=0)
    peso_previsto: float | None = Field(default=None, ge=0)


class LoadReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_carga: int
    id_operacao: int
    id_lote: int
    id_item_venda: int | None = None
    quantidade: float | None = None
    peso_previsto: float | None = None
    lote_codigo: str | None = None
    produto_nome: str | None = None
