from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ManutencaoCorretivaCreateSchema(BaseModel):
    id_manutencao: int
    defeito_relatado: str | None = None
    causa_raiz: str | None = None
    solucao_aplicada: str | None = None


class ManutencaoCorretivaUpdateSchema(BaseModel):
    defeito_relatado: str | None = None
    causa_raiz: str | None = None
    solucao_aplicada: str | None = None


class ManutencaoCorretivaReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_manutencao: int
    defeito_relatado: str | None
    causa_raiz: str | None
    solucao_aplicada: str | None
