"""Read-only options for phytosanitary UI until other modules own these APIs."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class PlantingOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_plantio: int
    produto_nome: str | None = None
    dt_plantio: date | None = None


class EmployeeOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_funcionario: int
    nome: str
    cargo: str | None = None
    setor: str | None = None


class InputOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_insumo: int
    nome: str
    classe_agronomica: str | None = None
    principio_ativo: str | None = None
    periodo_carencia_dias: int | None = None


class MachineOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_maquina: int
    nome: str | None = None
    status: str


class AgentOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_agente: int
    nome_comum: str | None = None
    nome_cientifico: str | None = None
    kind: str
