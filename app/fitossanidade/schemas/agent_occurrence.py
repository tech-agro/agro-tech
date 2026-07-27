from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AgentOccurrenceCreateSchema(BaseModel):
    """Nested POST body; control id comes from the URL."""

    id_agente: int
    nivel_infestacao: str | None = None
    metodo_controle: str | None = None


class AgentOccurrenceUpdateSchema(BaseModel):
    id_agente: int | None = None
    nivel_infestacao: str | None = None
    metodo_controle: str | None = None


class AgentOccurrenceReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_ocorrencia: int
    id_controle: int
    id_agente: int
    nivel_infestacao: str | None = None
    metodo_controle: str | None = None
    agente_nome: str | None = None
