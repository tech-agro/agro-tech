"""Enums do domínio financeiro (espelham tipos ENUM do Postgres)."""

from __future__ import annotations

import enum


class StatusContaReceber(str, enum.Enum):
    """Mirrors status_conta_receber_enum in the database."""

    ABERTA = "ABERTA"
    PARCIALMENTE_RECEBIDA = "PARCIALMENTE_RECEBIDA"
    RECEBIDA = "RECEBIDA"
    VENCIDA = "VENCIDA"
    CANCELADA = "CANCELADA"
