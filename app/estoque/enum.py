"""Enums do domínio estoque (espelham tipos ENUM do Postgres)."""

from __future__ import annotations

import enum


class StatusLote(str, enum.Enum):
    """Mirrors status_lote_enum in the database."""

    EM_ANALISE = "EM_ANALISE"
    LIBERADO = "LIBERADO"
    BLOQUEADO = "BLOQUEADO"


class LotOriginType(str, enum.Enum):
    """Mirrors tipo_origem_lote_enum in the database."""

    COLHEITA = "COLHEITA"
    COMPRA = "COMPRA"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"


class MovementType(str, enum.Enum):
    """Logical movement kinds (stored as VARCHAR; enum mirrors SQL type)."""

    ENTRADA_COMPRA = "entrada_compra"
    ENTRADA_COLHEITA = "entrada_colheita"
    SAIDA_VENDA = "saida_venda"
    SAIDA_ATIVIDADE = "saida_atividade"
    AJUSTE = "ajuste"
    TRANSFERENCIA = "transferencia"
