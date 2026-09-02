"""Purchases-specific labels and display helpers."""

from __future__ import annotations

from app.compras.enum import OrderStatus, PurchaseRequestStatus, PurchaseType
from app.compras.schemas.lookups import ProductOptionSchema, SupplierOptionSchema

STATUS_LABELS = {
    OrderStatus.ABERTO: "Aberto",
    OrderStatus.APROVADO: "Aprovado",
    OrderStatus.PARCIALMENTE_ATENDIDO: "Parcialmente atendido",
    OrderStatus.ATENDIDO: "Atendido",
    OrderStatus.CANCELADO: "Cancelado",
}

ORDER_STATUS_TONE = {
    "Aberto": "blue",
    "Aprovado": "orange",
    "Parcialmente atendido": "orange",
    "Atendido": "green",
    "Cancelado": "gray",
}

REQUEST_STATUS_LABELS = {
    PurchaseRequestStatus.RASCUNHO: "Rascunho",
    PurchaseRequestStatus.ENVIADA: "Enviada",
    PurchaseRequestStatus.APROVADA: "Aprovada",
    PurchaseRequestStatus.REJEITADA: "Rejeitada",
    PurchaseRequestStatus.CANCELADA: "Cancelada",
}

REQUEST_STATUS_TONE = {
    "Rascunho": "gray",
    "Enviada": "blue",
    "Aprovada": "green",
    "Rejeitada": "red",
    "Cancelada": "gray",
}

PURCHASE_TYPE_LABELS = {
    PurchaseType.INSUMO: "Insumo",
    PurchaseType.EQUIPAMENTO: "Equipamento",
}


ORDER_STATUS_OPTIONS = list(STATUS_LABELS.values())
REQUEST_STATUS_OPTIONS = list(REQUEST_STATUS_LABELS.values())


def order_status_label(status) -> str:
    return STATUS_LABELS.get(status, getattr(status, "value", str(status)))


def request_status_label(status) -> str:
    return REQUEST_STATUS_LABELS.get(status, getattr(status, "value", str(status)))


def product_unit(product: ProductOptionSchema) -> str:
    return product.unidade_sigla.value


def product_label(product: ProductOptionSchema) -> str:
    return product.nome


def supplier_label(supplier: SupplierOptionSchema) -> str:
    if supplier.categoria:
        return f"{supplier.nome} — {supplier.categoria}"
    return supplier.nome
