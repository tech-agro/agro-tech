from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PesticideApplicationCreateSchema(BaseModel):
    """Nested POST body; control id comes from the URL."""

    id_insumo: int
    dose_hectare: float | None = Field(default=None, gt=0)
    volume_aplicado: float | None = Field(default=None, gt=0)
    dt_aplicacao: date | None = None
    dt_carencia: date | None = None
    id_maquina: int | None = None

    @model_validator(mode="after")
    def validate_withdrawal_date(self) -> PesticideApplicationCreateSchema:
        if (
            self.dt_carencia is not None
            and self.dt_aplicacao is not None
            and self.dt_carencia < self.dt_aplicacao
        ):
            raise ValueError("dt_carencia must be on or after dt_aplicacao")
        return self


class PesticideApplicationUpdateSchema(BaseModel):
    id_insumo: int | None = None
    dose_hectare: float | None = Field(default=None, gt=0)
    volume_aplicado: float | None = Field(default=None, gt=0)
    dt_aplicacao: date | None = None
    dt_carencia: date | None = None
    id_maquina: int | None = None

    @model_validator(mode="after")
    def validate_withdrawal_date(self) -> PesticideApplicationUpdateSchema:
        if (
            self.dt_carencia is not None
            and self.dt_aplicacao is not None
            and self.dt_carencia < self.dt_aplicacao
        ):
            raise ValueError("dt_carencia must be on or after dt_aplicacao")
        return self


class PesticideApplicationReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_aplicacao: int
    id_controle: int
    id_insumo: int
    dose_hectare: float | None = None
    volume_aplicado: float | None = None
    dt_aplicacao: date | None = None
    dt_carencia: date | None = None
    id_maquina: int | None = None
    maquina_nome: str | None = None
    insumo_nome: str | None = None
