from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.manutencao.schemas.manutencao import ManutencaoReadSchema


class ManutencaoPreventivaCreateSchema(BaseModel):
    id_manutencao: int
    id_plano: int
    hodometro_execucao: float | None = Field(default=None, ge=0)
    proxima_hodometro: float | None = Field(default=None, ge=0)


class ManutencaoPreventivaUpdateSchema(BaseModel):
    dt_inicio: date | None = None
    id_plano: int | None = None
    hodometro_execucao: float | None = Field(default=None, ge=0)
    proxima_hodometro: float | None = Field(default=None, ge=0)


class ManutencaoPreventivaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_manutencao: int
    id_plano: int
    hodometro_execucao: float | None
    proxima_hodometro: float | None


class ManutencaoPreventivaDetalheSchema(BaseModel):
    manutencao: ManutencaoReadSchema
    preventiva: ManutencaoPreventivaReadSchema
    nome_maquina: str
    periodicidade: str | None = None
    proxima_execucao_plano: date | None = None
