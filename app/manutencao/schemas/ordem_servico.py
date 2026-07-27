from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

StatusOrdemServico = Literal["ABERTA", "EM_EXECUCAO", "CONCLUIDA", "CANCELADA"]


class OrdemServicoCreateSchema(BaseModel):
    id_manutencao: int
    descricao: str | None = None
    status: StatusOrdemServico


class OrdemServicoUpdateSchema(BaseModel):
    id_manutencao: int | None = None
    descricao: str | None = None
    status: StatusOrdemServico | None = None


class OrdemServicoReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_ordem_servico: int
    id_manutencao: int
    descricao: str | None
    status: str
