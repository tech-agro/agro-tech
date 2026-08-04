from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.logistica.enum import VehicleType


class VehicleCreateSchema(BaseModel):
    tipo: VehicleType
    placa: str = Field(min_length=1, max_length=15)
    capacidade: float | None = Field(default=None, ge=0)


class VehicleUpdateSchema(BaseModel):
    tipo: VehicleType | None = None
    placa: str | None = Field(default=None, min_length=1, max_length=15)
    capacidade: float | None = Field(default=None, ge=0)


class VehicleReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_veiculo: int
    tipo: VehicleType
    placa: str
    capacidade: float | None = None
