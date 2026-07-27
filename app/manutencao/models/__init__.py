"""Modelos ORM do dominio manutencao."""

from app.manutencao.models.manutencao import ManutencaoModel
from app.manutencao.models.manutencao_corretiva import ManutencaoCorretivaModel
from app.manutencao.models.manutencao_preventiva import ManutencaoPreventivaModel
from app.manutencao.models.ordem_servico import OrdemServicoModel
from app.manutencao.models.plano_manutencao import PlanoManutencaoModel

__all__ = [
    "ManutencaoCorretivaModel",
    "ManutencaoModel",
    "ManutencaoPreventivaModel",
    "OrdemServicoModel",
    "PlanoManutencaoModel",
]
