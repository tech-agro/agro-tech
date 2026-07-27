"""Enums do domínio estoque (espelham tipos ENUM do Postgres)."""

from __future__ import annotations

import enum


class StatusLote(str, enum.Enum):
    """Mirrors status_lote_enum in the database."""

    EM_ANALISE = "EM_ANALISE"
    LIBERADO = "LIBERADO"
    BLOQUEADO = "BLOQUEADO"
