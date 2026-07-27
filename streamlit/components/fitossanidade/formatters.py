"""Phytosanitary labels — one DB field each, no concatenated display strings."""

from __future__ import annotations

from app.fitossanidade.enum import AgentKind, SeverityLevel
from app.fitossanidade.schemas.lookups import (
    AgentOptionSchema,
    EmployeeOptionSchema,
    InputOptionSchema,
    MachineOptionSchema,
    PlantingOptionSchema,
)
from components.shared.formatters import is_blank

KIND_LABELS = {
    AgentKind.PEST: "Praga",
    AgentKind.DISEASE: "Doenca",
    "PRAGA": "Praga",
    "DOENCA": "Doenca",
}

# Streamlit 1.60 SelectboxColumn has no `placeholder`; use a PT sentinel option.
SELECT_PROMPT = "Selecione"

SEVERITY_OPTIONS = [
    SELECT_PROMPT,
    SeverityLevel.LOW.value,
    SeverityLevel.MEDIUM.value,
    SeverityLevel.HIGH.value,
    SeverityLevel.CRITICAL.value,
]
INFESTATION_OPTIONS = SEVERITY_OPTIONS


def is_unset(value) -> bool:
    if is_blank(value):
        return True
    text = str(value).strip()
    return text == "" or text == SELECT_PROMPT


def kind_label(kind: AgentKind | str) -> str:
    return KIND_LABELS.get(kind, str(kind))


def planting_label(planting: PlantingOptionSchema) -> str:
    return planting.produto_nome or f"#{planting.id_plantio}"


def employee_label(employee: EmployeeOptionSchema) -> str:
    return employee.nome


def agent_label(agent: AgentOptionSchema) -> str:
    return agent.nome_comum or agent.nome_cientifico or f"#{agent.id_agente}"


def input_label(inp: InputOptionSchema) -> str:
    if inp.classe_agronomica:
        return f"{inp.nome} ({inp.classe_agronomica})"
    return inp.nome


def machine_label(machine: MachineOptionSchema) -> str:
    return machine.nome or f"Maquina #{machine.id_maquina}"
