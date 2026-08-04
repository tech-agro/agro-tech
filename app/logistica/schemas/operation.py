from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.logistica.enum import OperationStatus, OperationType
from app.logistica.schemas.load import LoadCreateSchema


class OperationCreateSchema(BaseModel):
    id_veiculo: int
    id_origem: int
    id_destino: int
    id_venda: int | None = None
    tipo: OperationType = OperationType.VENDA
    custo_previsto: float | None = Field(default=None, ge=0)
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    status: OperationStatus = OperationStatus.ABERTA
    cargas: list[LoadCreateSchema] = Field(default_factory=list)
    suggest_loads_from_sale: bool = False

    @model_validator(mode="after")
    def validate_endpoints_and_period(self) -> OperationCreateSchema:
        if self.id_origem == self.id_destino:
            raise ValueError("origem and destino must be different")
        if (
            self.data_fim is not None
            and self.data_inicio is not None
            and self.data_fim < self.data_inicio
        ):
            raise ValueError("data_fim must be on or after data_inicio")
        if self.tipo == OperationType.VENDA and self.id_venda is None:
            raise ValueError("id_venda is required for VENDA operations")
        return self


class OperationUpdateSchema(BaseModel):
    id_veiculo: int | None = None
    id_origem: int | None = None
    id_destino: int | None = None
    id_venda: int | None = None
    tipo: OperationType | None = None
    custo_previsto: float | None = Field(default=None, ge=0)
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    status: OperationStatus | None = None

    @model_validator(mode="after")
    def validate_endpoints_and_period(self) -> OperationUpdateSchema:
        if (
            self.id_origem is not None
            and self.id_destino is not None
            and self.id_origem == self.id_destino
        ):
            raise ValueError("origem and destino must be different")
        if (
            self.data_fim is not None
            and self.data_inicio is not None
            and self.data_fim < self.data_inicio
        ):
            raise ValueError("data_fim must be on or after data_inicio")
        return self


class OperationReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_operacao: int
    id_veiculo: int
    id_origem: int
    id_destino: int
    id_venda: int | None = None
    tipo: OperationType = OperationType.VENDA
    custo_previsto: float | None = None
    data_inicio: datetime | None = None
    data_fim: datetime | None = None
    status: OperationStatus
    veiculo_placa: str | None = None
    origem_nome: str | None = None
    destino_nome: str | None = None
    cliente_nome: str | None = None
