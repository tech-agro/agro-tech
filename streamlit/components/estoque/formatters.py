"""Funções auxiliares para exibição de rótulos no módulo de estoque."""

from __future__ import annotations

from app.core.enum import StatusCertificacao
from app.estoque.schemas.lookups import (
    CertificacaoOptionSchema,
    ColheitaOptionSchema,
    EstoqueOptionSchema,
    ItemPedidoOptionSchema,
    LocalArmazenamentoOptionSchema,
    LoteOptionSchema,
    ProdutoOptionSchema,
)

STATUS_LABELS: dict[StatusCertificacao, str] = {
    StatusCertificacao.VIGENTE: "Vigente",
    StatusCertificacao.VENCIDA: "Vencida",
    StatusCertificacao.SUSPENSA: "Suspensa",
    StatusCertificacao.CANCELADA: "Cancelada",
}


def produto_label(option: ProdutoOptionSchema) -> str:
    return f"{option.nome} (#{option.id_produto})"


def local_label(option: LocalArmazenamentoOptionSchema) -> str:
    return f"{option.descricao} (#{option.id_local})"


def estoque_label(option: EstoqueOptionSchema) -> str:
    return f"{option.descricao} (#{option.id_estoque})"


def lote_label(option: LoteOptionSchema) -> str:
    if option.produto_nome:
        return f"{option.codigo_lote} — {option.produto_nome}"
    return option.codigo_lote


def certificacao_label(option: CertificacaoOptionSchema) -> str:
    return option.nome


def colheita_label(option: ColheitaOptionSchema) -> str:
    return option.label


def item_pedido_label(option: ItemPedidoOptionSchema) -> str:
    return option.descricao