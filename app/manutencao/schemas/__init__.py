"""Schemas do dominio manutencao."""

from app.manutencao.schemas.manutencao import (
    ManutencaoCreateSchema,
    ManutencaoReadSchema,
    ManutencaoUpdateSchema,
)
from app.manutencao.schemas.manutencao_corretiva import (
    ManutencaoCorretivaCreateSchema,
    ManutencaoCorretivaReadSchema,
    ManutencaoCorretivaUpdateSchema,
)
from app.manutencao.schemas.manutencao_preventiva import (
    ManutencaoPreventivaCreateSchema,
    ManutencaoPreventivaReadSchema,
    ManutencaoPreventivaUpdateSchema,
)
from app.manutencao.schemas.ordem_servico import (
    OrdemServicoCreateSchema,
    OrdemServicoReadSchema,
    OrdemServicoUpdateSchema,
)
from app.manutencao.schemas.plano_manutencao import (
    PlanoManutencaoCreateSchema,
    PlanoManutencaoReadSchema,
    PlanoManutencaoUpdateSchema,
)

__all__ = [
    "ManutencaoCorretivaCreateSchema",
    "ManutencaoCorretivaReadSchema",
    "ManutencaoCorretivaUpdateSchema",
    "ManutencaoCreateSchema",
    "ManutencaoPreventivaCreateSchema",
    "ManutencaoPreventivaReadSchema",
    "ManutencaoPreventivaUpdateSchema",
    "ManutencaoReadSchema",
    "ManutencaoUpdateSchema",
    "OrdemServicoCreateSchema",
    "OrdemServicoReadSchema",
    "OrdemServicoUpdateSchema",
    "PlanoManutencaoCreateSchema",
    "PlanoManutencaoReadSchema",
    "PlanoManutencaoUpdateSchema",
]
