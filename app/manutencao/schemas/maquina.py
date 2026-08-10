from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MaquinaCreateSchema(BaseModel):
    id_tipo_maquina: int
    nome: str = Field(min_length=1, max_length=255)
    status: str = Field(min_length=1, max_length=50)


class MaquinaUpdateSchema(BaseModel):
    id_tipo_maquina: int | None = None
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, min_length=1, max_length=50)


class MaquinaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_maquina: int
    id_tipo_maquina: int
    id_fazenda: int
    nome: str
    status: str
    nome_fazenda: str | None = None
    descricao_tipo: str | None = None