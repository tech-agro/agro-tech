from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WeighingCreateSchema(BaseModel):
    """Nested POST body; load id comes from the URL."""

    peso_registrado: float | None = Field(default=None, ge=0)
    data_pesagem: datetime | None = None


class WeighingUpdateSchema(BaseModel):
    peso_registrado: float | None = Field(default=None, ge=0)
    data_pesagem: datetime | None = None


class WeighingReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pesagem: int
    id_carga: int
    peso_registrado: float | None = None
    data_pesagem: datetime | None = None
