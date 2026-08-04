"""Internal DTOs returned by connectors (provider JSON stays inside clients)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    """Normalized weather snapshot from Open-Meteo (#75)."""

    temperature_c: float | None = None
    humidity_pct: float | None = None
    precipitation_mm: float | None = None
    latitude: float | None = None
    longitude: float | None = None


class MarketPriceData(BaseModel):
    """Normalized commodity quote from AgroDoc / CEPEA (#76)."""

    product: str
    price: Decimal
    unit: str | None = None
    source: str | None = None
    updated_at: str | None = None


class AddressData(BaseModel):
    """Normalized address from ViaCEP (#77)."""

    cep: str
    logradouro: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    localidade: str | None = None
    uf: str | None = Field(default=None, min_length=2, max_length=2)


class CompanyData(BaseModel):
    """Normalized company registry data from BrasilAPI CNPJ (#78)."""

    cnpj: str
    razao_social: str | None = None
    nome_fantasia: str | None = None
    situacao_cadastral: str | None = None
    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    bairro: str | None = None
    municipio: str | None = None
    uf: str | None = None
