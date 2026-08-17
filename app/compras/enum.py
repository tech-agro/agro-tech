"""Purchase domain enums (DB values stay in Portuguese)."""

from __future__ import annotations

import enum


class OrderStatus(str, enum.Enum):
    """Mirrors status_pedido_compra_enum in the database."""

    ABERTO = "ABERTO"
    APROVADO = "APROVADO"
    PARCIALMENTE_ATENDIDO = "PARCIALMENTE_ATENDIDO"
    ATENDIDO = "ATENDIDO"
    CANCELADO = "CANCELADO"


class PurchaseRequestStatus(str, enum.Enum):
    """Mirrors status_solicitacao_compra_enum."""

    RASCUNHO = "RASCUNHO"
    ENVIADA = "ENVIADA"
    APROVADA = "APROVADA"
    REJEITADA = "REJEITADA"
    CANCELADA = "CANCELADA"


class PurchaseType(str, enum.Enum):
    """Mirrors tipo_compra_enum."""

    INSUMO = "INSUMO"
    EQUIPAMENTO = "EQUIPAMENTO"


class QuotationStatus(str, enum.Enum):
    """Mirrors status_cotacao_compra_enum."""

    RASCUNHO = "RASCUNHO"
    ENVIADA = "ENVIADA"
    VENCEDORA = "VENCEDORA"
    DESCARTADA = "DESCARTADA"
