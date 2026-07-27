from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UsoMaquinaCreateSchema(BaseModel):
    id_maquina: int
    id_atividade: int
    dt_inicio: datetime
    dt_fim: datetime
    horas_trabalhadas: float = Field(ge=0)


class UsoMaquinaUpdateSchema(BaseModel):
    id_maquina: int | None = None
    id_atividade: int | None = None
    dt_inicio: datetime | None = None
    dt_fim: datetime | None = None
    horas_trabalhadas: float | None = Field(default=None, ge=0)


class UsoMaquinaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_uso: int
    id_maquina: int
    id_atividade: int
    dt_inicio: datetime
    dt_fim: datetime
    horas_trabalhadas: float