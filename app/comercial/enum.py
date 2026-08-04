"""Catalog enums (DB values stay constrained / Portuguese naming in SQL)."""

from __future__ import annotations

import enum


class UnitSymbol(str, enum.Enum):
    """Mirrors unidade_sigla_enum in the database."""

    KG = "KG"
    L = "L"
    UN = "UN"
    SC = "SC"
    HA = "HA"
    T = "T"


class StatusCliente(str, enum.Enum):
    """Mirrors status_cliente_enum in the database."""

    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    BLOQUEADO = "BLOQUEADO"
