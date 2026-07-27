from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatusManutencao = Literal["ABERTA", "EM_EXECUCAO", "CONCLUIDA", "CANCELADA"]


class ManutencaoCreateSchema(BaseModel):
    id_maquina: int
    id_funcionario: int | None = None
    id_prestador: int | None = None
    tipo: str | None = Field(default=None, max_length=50)
    custo: float | None = Field(default=None, ge=0)
    status: StatusManutencao
    dt_inicio: date | None = None
    dt_fim: date | None = None


class ManutencaoUpdateSchema(BaseModel):
    id_maquina: int | None = None
    id_funcionario: int | None = None
    id_prestador: int | None = None
    tipo: str | None = Field(default=None, max_length=50)
    custo: float | None = Field(default=None, ge=0)
    status: StatusManutencao | None = None
    dt_inicio: date | None = None
    dt_fim: date | None = None


class ManutencaoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_manutencao: int
    id_maquina: int
    id_funcionario: int | None
    id_prestador: int | None
    tipo: str | None
    custo: float | None
    status: str
    dt_inicio: date | None
    dt_fim: date | None
