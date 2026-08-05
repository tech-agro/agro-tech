from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PlanoManutencaoCreateSchema(BaseModel):
    id_maquina: int
    periodicidade: str | None = Field(default=None, max_length=80)
    proxima_execucao: date | None = None


class PlanoManutencaoUpdateSchema(BaseModel):
    id_maquina: int | None = None
    periodicidade: str | None = Field(default=None, max_length=80)
    proxima_execucao: date | None = None


class PlanoManutencaoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_plano: int
    id_maquina: int
    periodicidade: str | None
    proxima_execucao: date | None


class PlanoManutencaoDetalheSchema(BaseModel):
    id_plano: int
    id_maquina: int
    periodicidade: str | None
    proxima_execucao: date | None
    nome_maquina: str
