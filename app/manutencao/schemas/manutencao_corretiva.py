from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


from app.manutencao.schemas.manutencao import ManutencaoReadSchema


class ManutencaoCorretivaCreateSchema(BaseModel):
    id_manutencao: int
    defeito_relatado: str | None = None
    causa_raiz: str | None = None
    solucao_aplicada: str | None = None


class ManutencaoCorretivaUpdateSchema(BaseModel):
    dt_inicio: date | None = None
    defeito_relatado: str | None = None
    causa_raiz: str | None = None
    solucao_aplicada: str | None = None


class ManutencaoCorretivaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_manutencao: int
    defeito_relatado: str | None
    causa_raiz: str | None
    solucao_aplicada: str | None


class ManutencaoCorretivaDetalheSchema(BaseModel):
    manutencao: ManutencaoReadSchema
    corretiva: ManutencaoCorretivaReadSchema
    nome_maquina: str
