from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AbastecimentoCreateSchema(BaseModel):
    id_maquina: int
    combustivel: str = Field(min_length=1, max_length=50)
    litros: float = Field(gt=0)
    valor: float = Field(ge=0)
    horimetro: float = Field(ge=0)
    dt_abastecimento: datetime


class AbastecimentoUpdateSchema(BaseModel):
    id_maquina: int | None = None
    combustivel: str | None = Field(default=None, min_length=1, max_length=50)
    litros: float | None = Field(default=None, gt=0)
    valor: float | None = Field(default=None, ge=0)
    horimetro: float | None = Field(default=None, ge=0)
    dt_abastecimento: datetime | None = None


class AbastecimentoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_abastecimento: int
    id_maquina: int
    combustivel: str
    litros: float
    valor: float
    horimetro: float
    dt_abastecimento: datetime