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

REQUEST_STATUS_LABELS = {
    PurchaseRequestStatus.RASCUNHO: "Rascunho",
    PurchaseRequestStatus.ENVIADA: "Enviada",
    PurchaseRequestStatus.APROVADA: "Aprovada",
    PurchaseRequestStatus.REJEITADA: "Rejeitada",
    PurchaseRequestStatus.CANCELADA: "Cancelada",
}

PURCHASE_TYPE_LABELS = {
    PurchaseType.INSUMO: "Insumo",
    PurchaseType.EQUIPAMENTO: "Equipamento",
}


def product_unit(product: ProductOptionSchema) -> str:
    return product.unidade_sigla.value


def product_label(product: ProductOptionSchema) -> str:
    return product.nome


def supplier_label(supplier: SupplierOptionSchema) -> str:
    if supplier.categoria:
        return f"{supplier.nome} — {supplier.categoria}"
    return supplier.nome
