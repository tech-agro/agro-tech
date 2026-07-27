"""Schemas Pydantic do dominio inteligencia."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class IndicadorCreateSchema(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    unidade: str | None = Field(default=None, max_length=30)


class IndicadorUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    unidade: str | None = Field(default=None, max_length=30)


class IndicadorReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_indicador: int
    nome: str
    unidade: str | None


class MedicaoIndicadorCreateSchema(BaseModel):
    id_indicador: int
    id_safra: int
    valor: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    data_referencia: date | None = None


class MedicaoIndicadorUpdateSchema(BaseModel):
    id_indicador: int | None = None
    id_safra: int | None = None
    valor: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    data_referencia: date | None = None


class MedicaoIndicadorReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_medicao: int
    id_indicador: int
    id_safra: int
    valor: Decimal | None
    data_referencia: date | None
    indicador_nome: str | None = None
    safra_nome: str | None = None
