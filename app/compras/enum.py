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
