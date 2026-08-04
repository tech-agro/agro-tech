from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.logistica.enum import LocationType
from app.logistica.schemas.address import AddressCreateSchema, AddressReadSchema


class LocationCreateSchema(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    tipo: LocationType
    endereco: AddressCreateSchema | None = None
    id_endereco: int | None = None
    id_local_armazenamento: int | None = None


class LocationUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    tipo: LocationType | None = None
    id_endereco: int | None = None
    id_local_armazenamento: int | None = None
    endereco: AddressCreateSchema | None = None


class LocationReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_local_logistico: int
    nome: str
    tipo: LocationType
    id_endereco: int | None = None
    id_local_armazenamento: int | None = None
    endereco: AddressReadSchema | None = None
