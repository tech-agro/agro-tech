"""Read-only options for logistics UI until other modules own these APIs."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.logistica.enum import LocationType, VehicleType


class VehicleTypeOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo: VehicleType


class VehicleOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_veiculo: int
    placa: str
    tipo: VehicleType
    capacidade: float | None = None


class LocationOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_local_logistico: int
    nome: str
    tipo: LocationType


class SaleOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_venda: int
    cliente_nome: str | None = None
    data_venda: date | None = None
    valor_total: float


class LotOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_lote: int
    codigo_lote: str
    produto_nome: str | None = None


class DriverOptionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_funcionario: int
    nome: str
    cargo: str | None = None
    setor: str | None = None
