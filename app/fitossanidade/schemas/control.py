from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.fitossanidade.schemas.agent_occurrence import AgentOccurrenceCreateSchema


class ControlCreateSchema(BaseModel):
    id_plantio: int
    id_funcionario: int
    dt_identificacao: date | None = None
    nivel_severidade: str | None = None
    area_afetada_hectares: float | None = Field(default=None, ge=0)
    recomendacao: str | None = None
    ocorrencias: list[AgentOccurrenceCreateSchema] = Field(default_factory=list)


class ControlUpdateSchema(BaseModel):
    id_plantio: int | None = None
    id_funcionario: int | None = None
    dt_identificacao: date | None = None
    nivel_severidade: str | None = None
    area_afetada_hectares: float | None = Field(default=None, ge=0)
    recomendacao: str | None = None


class ControlReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_controle: int
    id_plantio: int
    id_funcionario: int
    dt_identificacao: date | None = None
    nivel_severidade: str | None = None
    area_afetada_hectares: float | None = None
    recomendacao: str | None = None
    plantio_produto_nome: str | None = None
    funcionario_nome: str | None = None
