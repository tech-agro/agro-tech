"""Phytosanitary domain enums (API values; specialization is stored in tables)."""

from __future__ import annotations

import enum


class AgentKind(str, enum.Enum):
    """Total disjoint specialization of agente_nocivo."""

    PEST = "PRAGA"
    DISEASE = "DOENCA"


class SeverityLevel(str, enum.Enum):
    """Shared scale for control severity and occurrence infestation level."""

    LOW = "Baixo"
    MEDIUM = "Medio"
    HIGH = "Alto"
    CRITICAL = "Critico"


SEVERITY_RANK: dict[str, int] = {
    SeverityLevel.LOW.value: 1,
    SeverityLevel.MEDIUM.value: 2,
    SeverityLevel.HIGH.value: 3,
    SeverityLevel.CRITICAL.value: 4,
}

# Agronomic classes treated as pesticides (defensivos) for lookup/validation.
PESTICIDE_CLASSES: frozenset[str] = frozenset(
    {
        "Herbicida",
        "Inseticida",
        "Fungicida",
        "Acaricida",
        "Nematicida",
        "Bactericida",
        "Defensivo",
    }
)

DEFENSIVE_CATEGORY_NAME = "Defensivos"
