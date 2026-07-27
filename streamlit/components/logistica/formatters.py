"""Logistics labels — one DB field each."""

from __future__ import annotations

from app.logistica.enum import (
    DispatchStatus,
    LocationType,
    OperationStatus,
    OperationType,
    VehicleType,
)
from app.logistica.schemas.lookups import (
    DriverOptionSchema,
    LocationOptionSchema,
    LotOptionSchema,
    SaleOptionSchema,
    VehicleOptionSchema,
)

OPERATION_STATUS_LABELS = {
    OperationStatus.ABERTA: "Aberta",
    OperationStatus.EM_ANDAMENTO: "Em andamento",
    OperationStatus.CONCLUIDA: "Concluida",
    OperationStatus.CANCELADA: "Cancelada",
}

OPERATION_TYPE_LABELS = {
    OperationType.VENDA: "Venda",
    OperationType.COMPRA: "Compra",
    OperationType.TRANSFERENCIA: "Transferencia",
    OperationType.SERVICO: "Servico",
}

DISPATCH_STATUS_LABELS = {
    DispatchStatus.PENDENTE: "Pendente",
    DispatchStatus.EM_PREPARACAO: "Em preparacao",
    DispatchStatus.EXPEDIDA: "Expedida",
    DispatchStatus.ENTREGUE: "Entregue",
    DispatchStatus.CANCELADA: "Cancelada",
}

LOCATION_TYPE_LABELS = {
    LocationType.FAZENDA: "Fazenda",
    LocationType.ARMAZEM: "Armazem",
    LocationType.CLIENTE: "Cliente",
    LocationType.FORNECEDOR: "Fornecedor",
    LocationType.PORTO: "Porto",
    LocationType.COOPERATIVA: "Cooperativa",
    LocationType.OFICINA: "Oficina",
    LocationType.PATIO: "Patio",
    LocationType.CENTRO_DISTRIBUICAO: "Centro de distribuicao",
    LocationType.OUTRO: "Outro",
}

VEHICLE_TYPE_LABELS = {
    VehicleType.CAMINHAO_GRANELEIRO: "Caminhao graneleiro",
    VehicleType.CAMINHAO_BASCULANTE: "Caminhao basculante",
    VehicleType.CAMINHAO_BAU: "Caminhao bau",
    VehicleType.CAMINHAO_TANQUE: "Caminhao tanque",
    VehicleType.CARRETA_BASCULANTE: "Carreta basculante",
    VehicleType.BITREM: "Bitrem",
    VehicleType.RODOTREM: "Rodotrem",
    VehicleType.TOCO: "Toco",
    VehicleType.TRUCK: "Truck",
    VehicleType.CAMIONETE: "Camionete",
    VehicleType.UTILITARIO: "Utilitario",
    VehicleType.VAN: "Van",
    VehicleType.TRATOR: "Trator",
    VehicleType.OUTRO: "Outro",
}


def vehicle_type_label(tipo: VehicleType | str) -> str:
    if isinstance(tipo, VehicleType):
        return VEHICLE_TYPE_LABELS.get(tipo, tipo.value)
    try:
        return VEHICLE_TYPE_LABELS.get(VehicleType(tipo), str(tipo))
    except ValueError:
        return str(tipo)


def vehicle_label(item: VehicleOptionSchema) -> str:
    return item.placa


def location_label(item: LocationOptionSchema) -> str:
    return item.nome


def location_type_label(tipo: LocationType | str) -> str:
    if isinstance(tipo, LocationType):
        return LOCATION_TYPE_LABELS.get(tipo, tipo.value)
    try:
        return LOCATION_TYPE_LABELS.get(LocationType(tipo), str(tipo))
    except ValueError:
        return str(tipo)


def sale_label(item: SaleOptionSchema) -> str:
    cliente = item.cliente_nome or "Cliente"
    data = item.data_venda.isoformat() if item.data_venda else "—"
    return f"#{item.id_venda} — {cliente} ({data})"


def lot_label(item: LotOptionSchema) -> str:
    if item.produto_nome:
        return f"{item.codigo_lote} ({item.produto_nome})"
    return item.codigo_lote


def driver_label(item: DriverOptionSchema) -> str:
    return item.nome
