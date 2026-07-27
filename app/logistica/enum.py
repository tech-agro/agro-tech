"""Logistics domain enums (DB values stay in Portuguese)."""

from __future__ import annotations

import enum


class OperationStatus(str, enum.Enum):
    """Mirrors status_operacao_logistica_enum in the database.

    Visao gerencial da operacao (complementa status_expedicao_enum).
    """

    ABERTA = "ABERTA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class OperationType(str, enum.Enum):
    """Mirrors tipo_operacao_logistica_enum in the database."""

    VENDA = "VENDA"
    COMPRA = "COMPRA"
    TRANSFERENCIA = "TRANSFERENCIA"
    SERVICO = "SERVICO"


class DispatchStatus(str, enum.Enum):
    """Mirrors status_expedicao_enum in the database."""

    PENDENTE = "PENDENTE"
    EM_PREPARACAO = "EM_PREPARACAO"
    EXPEDIDA = "EXPEDIDA"
    ENTREGUE = "ENTREGUE"
    CANCELADA = "CANCELADA"


class LocationType(str, enum.Enum):
    """Mirrors tipo_local_logistico_enum in the database."""

    FAZENDA = "FAZENDA"
    ARMAZEM = "ARMAZEM"
    CLIENTE = "CLIENTE"
    FORNECEDOR = "FORNECEDOR"
    PORTO = "PORTO"
    COOPERATIVA = "COOPERATIVA"
    OFICINA = "OFICINA"
    PATIO = "PATIO"
    CENTRO_DISTRIBUICAO = "CENTRO_DISTRIBUICAO"
    OUTRO = "OUTRO"


class VehicleType(str, enum.Enum):
    """Mirrors tipo_veiculo_enum in the database."""

    CAMINHAO_GRANELEIRO = "CAMINHAO_GRANELEIRO"
    CAMINHAO_BASCULANTE = "CAMINHAO_BASCULANTE"
    CAMINHAO_BAU = "CAMINHAO_BAU"
    CAMINHAO_TANQUE = "CAMINHAO_TANQUE"
    CARRETA_BASCULANTE = "CARRETA_BASCULANTE"
    BITREM = "BITREM"
    RODOTREM = "RODOTREM"
    TOCO = "TOCO"
    TRUCK = "TRUCK"
    CAMIONETE = "CAMIONETE"
    UTILITARIO = "UTILITARIO"
    VAN = "VAN"
    TRATOR = "TRATOR"
    OUTRO = "OUTRO"
