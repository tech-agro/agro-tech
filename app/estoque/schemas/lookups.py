"""Schemas Pydantic para lookups do módulo de estoque."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProdutoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_produto: int
    nome: str


class ColheitaOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_colheita: int
    label: str


class LocalArmazenamentoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_local: int
    descricao: str


class EstoqueOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_estoque: int
    descricao: str


class LoteOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_lote: int
    codigo_lote: str
    produto_nome: str | None = None


class CertificacaoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_certificacao: int
    nome: str


class ItemPedidoOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_item_pedido: int
    descricao: str