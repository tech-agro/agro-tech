from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TipoMaquinaCreateSchema(BaseModel):
    descricao: str = Field(min_length=1, max_length=255)


class TipoMaquinaUpdateSchema(BaseModel):
    descricao: str | None = Field(default=None, min_length=1, max_length=255)


class TipoMaquinaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_tipo_maquina: int
    descricao: str