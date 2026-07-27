from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.fitossanidade.enum import AgentKind


class PestCreateSchema(BaseModel):
    nome_comum: str | None = None
    nome_cientifico: str | None = None
    tipo_praga: str | None = None
    habito_alimentar: str | None = None


class DiseaseCreateSchema(BaseModel):
    nome_comum: str | None = None
    nome_cientifico: str | None = None
    agente_causador: str | None = None
    sintomas: str | None = None
    condicao_favoravel: str | None = None


class HarmfulAgentUpdateSchema(BaseModel):
    nome_comum: str | None = None
    nome_cientifico: str | None = None
    # Pest specialization (ignored when agent is a disease)
    tipo_praga: str | None = None
    habito_alimentar: str | None = None
    # Disease specialization (ignored when agent is a pest)
    agente_causador: str | None = None
    sintomas: str | None = None
    condicao_favoravel: str | None = None


class HarmfulAgentReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_agente: int
    nome_comum: str | None = None
    nome_cientifico: str | None = None
    kind: AgentKind
    tipo_praga: str | None = None
    habito_alimentar: str | None = None
    agente_causador: str | None = None
    sintomas: str | None = None
    condicao_favoravel: str | None = None
