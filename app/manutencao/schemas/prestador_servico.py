from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PrestadorServicoCreateSchema(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    cnpj: str = Field(min_length=14, max_length=18)
    especialidade: str = Field(min_length=1, max_length=100)
    telefone: str = Field(min_length=8, max_length=20)


class PrestadorServicoUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    cnpj: str | None = Field(default=None, min_length=14, max_length=18)
    especialidade: str | None = Field(default=None, min_length=1, max_length=100)
    telefone: str | None = Field(default=None, min_length=8, max_length=20)


class PrestadorServicoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_prestador: int
    nome: str
    cnpj: str
    especialidade: str
    telefone: str