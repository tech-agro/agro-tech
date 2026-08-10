from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.integrations.schemas import AddressData


class AddressLookupSchema(BaseModel):
    """Address fields returned by CEP lookup for form autofill."""

    cep: str
    logradouro: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    estado: str | None = None

    @classmethod
    def from_address_data(cls, data: AddressData) -> AddressLookupSchema:
        return cls(
            cep=data.cep,
            logradouro=data.logradouro,
            complemento=data.complemento,
            bairro=data.bairro,
            cidade=data.localidade,
            estado=data.uf,
        )


class AddressCreateSchema(BaseModel):
    logradouro: str = Field(min_length=1, max_length=255)
    numero: str | None = Field(default=None, max_length=30)
    cidade: str = Field(min_length=1, max_length=120)
    estado: str = Field(min_length=2, max_length=2)
    cep: str | None = Field(default=None, max_length=12)
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    @field_validator("estado")
    @classmethod
    def normalize_estado(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if len(cleaned) != 2 or not cleaned.isalpha():
            raise ValueError("estado must be a 2-letter UF")
        return cleaned


class AddressUpdateSchema(BaseModel):
    logradouro: str | None = Field(default=None, min_length=1, max_length=255)
    numero: str | None = Field(default=None, max_length=30)
    cidade: str | None = Field(default=None, min_length=1, max_length=120)
    estado: str | None = Field(default=None, min_length=2, max_length=2)
    cep: str | None = Field(default=None, max_length=12)
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    @field_validator("estado")
    @classmethod
    def normalize_estado(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        if len(cleaned) != 2 or not cleaned.isalpha():
            raise ValueError("estado must be a 2-letter UF")
        return cleaned


class AddressReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_endereco: int
    logradouro: str
    numero: str | None = None
    cidade: str
    estado: str
    cep: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
