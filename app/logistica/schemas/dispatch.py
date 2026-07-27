from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.logistica.enum import DispatchStatus


class DispatchCreateSchema(BaseModel):
    """Nested POST body; load id comes from the URL (1:1 with carga)."""

    data_saida: datetime | None = None
    data_chegada_prevista: datetime | None = None
    data_entrega: datetime | None = None
    id_funcionario: int | None = None
    observacoes: str | None = None
    status: DispatchStatus | None = None


class DispatchUpdateSchema(BaseModel):
    data_saida: datetime | None = None
    data_chegada_prevista: datetime | None = None
    data_entrega: datetime | None = None
    id_funcionario: int | None = None
    observacoes: str | None = None
    status: DispatchStatus | None = None


class DispatchReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_expedicao: int
    id_carga: int
    data_saida: datetime | None = None
    data_chegada_prevista: datetime | None = None
    data_entrega: datetime | None = None
    id_funcionario: int | None = None
    motorista_nome: str | None = None
    observacoes: str | None = None
    status: DispatchStatus
