from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ManutencaoPreventivaCreateSchema(BaseModel):
    id_manutencao: int
    id_plano: int
    hodometro_execucao: float | None = Field(default=None, ge=0)
    proxima_hodometro: float | None = Field(default=None, ge=0)


class ManutencaoPreventivaUpdateSchema(BaseModel):
    id_plano: int | None = None
    hodometro_execucao: float | None = Field(default=None, ge=0)
    proxima_hodometro: float | None = Field(default=None, ge=0)


class ManutencaoPreventivaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_manutencao: int
    id_plano: int
    hodometro_execucao: float | None
    proxima_hodometro: float | None
