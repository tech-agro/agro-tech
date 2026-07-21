"""Purchase domain use cases."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from app.compras.enum import OrderStatus
from app.compras.errors import PurchaseError
from app.compras.models.order import OrderModel
from app.compras.models.order_item import OrderItemModel
from app.compras.repository import (
    OrderItemRepository,
    OrderRepository,
    PurchaseLookupRepository,
    PurchaseRepository,
)
from app.compras.schemas.lookups import (
    CostCenterOptionSchema,
    ProductOptionSchema,
    SupplierOptionSchema,
)
from app.compras.schemas.order import (
    OrderCreateSchema,
    OrderReadSchema,
    OrderUpdateSchema,
)
from app.compras.schemas.order_item import (
    OrderItemCreateSchema,
    OrderItemReadSchema,
    OrderItemUpdateSchema,
)
from app.compras.schemas.purchase import (
    PurchaseCreateSchema,
    PurchaseReadSchema,
    PurchaseUpdateSchema,
)
from app.core.database import get_session

if TYPE_CHECKING:
    from app.estoque.service import EstoqueService

_EDITABLE_STATUSES = frozenset({OrderStatus.ABERTO})
_PURCHASE_ALLOWED_STATUSES = frozenset({OrderStatus.APROVADO})


class PurchaseService:
    """Orchestrates orders, items, and purchases. External integrations are hooks."""

    def __init__(
        self,
        order_repo: OrderRepository | None = None,
        item_repo: OrderItemRepository | None = None,
        purchase_repo: PurchaseRepository | None = None,
        lookup_repo: PurchaseLookupRepository | None = None,
        inventory_service: EstoqueService | None = None,
    ) -> None:
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
        self.purchase_repo = purchase_repo or PurchaseRepository()
        self.lookup_repo = lookup_repo or PurchaseLookupRepository()
        self._inventory_service = inventory_service

    def _inventory(self) -> EstoqueService:
        if self._inventory_service is None:
            from app.estoque.service import EstoqueService

            self._inventory_service = EstoqueService()
        return self._inventory_service

    def _get_order_model(self, order_id: int):
        return self.order_repo.get_by_id(order_id)

    def _ensure_order_editable(self, order_id: int):
        order = self._get_order_model(order_id)
        if order is None:
            return None
        if order.status not in _EDITABLE_STATUSES:
            raise PurchaseError(
                f"Order in status {order.status.value} does not allow item changes"
            )
        return order

    def _request_stock_entry(self, purchase_id: int) -> None:
        """Stock entry belongs to the inventory domain (when implemented)."""
        self._inventory().register_entry_from_purchase(purchase_id)

    @staticmethod
    def _to_order_read(order: OrderModel, fornecedor_nome: str | None) -> OrderReadSchema:
        data = OrderReadSchema.model_validate(order).model_dump()
        data["fornecedor_nome"] = fornecedor_nome
        return OrderReadSchema.model_validate(data)

    @staticmethod
    def _to_item_read(
        item: OrderItemModel, produto_nome: str | None, unidade_sigla
    ) -> OrderItemReadSchema:
        data = OrderItemReadSchema.model_validate(item).model_dump()
        data["produto_nome"] = produto_nome
        data["unidade_sigla"] = unidade_sigla
        return OrderItemReadSchema.model_validate(data)

    def _load_order_read(self, order_id: int) -> OrderReadSchema | None:
        loaded = self.order_repo.get_with_supplier_name(order_id)
        if loaded is None:
            return None
        order, nome = loaded
        return self._to_order_read(order, nome)

    def _load_item_read(self, item_id: int) -> OrderItemReadSchema | None:
        loaded = self.item_repo.get_with_product_labels(item_id)
        if loaded is None:
            return None
        item, nome, sigla = loaded
        return self._to_item_read(item, nome, sigla)

    # --- Lookups (shared catalog read until other modules expose APIs) ---

    def list_product_options(self) -> list[ProductOptionSchema]:
        return [
            ProductOptionSchema(
                id_produto=produto.id_produto,
                nome=produto.nome,
                unidade_sigla=unidade.sigla,
                unidade_descricao=unidade.descricao,
            )
            for produto, unidade in self.lookup_repo.list_products()
        ]

    def list_supplier_options(self) -> list[SupplierOptionSchema]:
        return [
            SupplierOptionSchema(
                id_fornecedor=fornecedor.id_fornecedor,
                nome=nome,
                categoria=fornecedor.categoria,
            )
            for fornecedor, nome in self.lookup_repo.list_suppliers()
        ]

    def list_cost_center_options(self) -> list[CostCenterOptionSchema]:
        return [
            CostCenterOptionSchema.model_validate(row)
            for row in self.lookup_repo.list_cost_centers()
        ]

    # --- Orders ---

    def create_order(self, payload: OrderCreateSchema) -> OrderReadSchema:
        """Create order header and at least one item in a single transaction."""
        header = payload.model_dump(exclude={"itens"})
        try:
            with get_session() as session:
                order = OrderModel(**header)
                session.add(order)
                session.flush()
                order_id = order.id_pedido
                for item in payload.itens:
                    session.add(
                        OrderItemModel(id_pedido=order_id, **item.model_dump())
                    )
                session.flush()
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not create order. Check that id_fornecedor and id_produto exist."
            ) from exc
        loaded = self._load_order_read(order_id)
        assert loaded is not None
        return loaded

    def list_orders(self) -> list[OrderReadSchema]:
        return [
            self._to_order_read(order, nome)
            for order, nome in self.order_repo.list_with_supplier_name()
        ]

    def get_order(self, order_id: int) -> OrderReadSchema | None:
        return self._load_order_read(order_id)

    def update_order(
        self, order_id: int, payload: OrderUpdateSchema
    ) -> OrderReadSchema | None:
        previous = self._get_order_model(order_id)
        if previous is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        new_status = data.get("status")
        approving = (
            new_status == OrderStatus.APROVADO
            and previous.status != OrderStatus.APROVADO
        )
        if approving:
            self._assert_can_auto_purchase(order_id)

        record = self.order_repo.update(order_id, data)
        if record is None:
            return None

        if approving:
            self._register_purchase_on_approval(order_id)

        return self._load_order_read(order_id)

    def _assert_can_auto_purchase(self, order_id: int) -> None:
        if self.purchase_repo.list(filters={"id_pedido": order_id}):
            return
        if not self.item_repo.list(filters={"id_pedido": order_id}):
            raise PurchaseError("An order without items cannot generate a purchase")
        if not self.lookup_repo.list_cost_centers():
            raise PurchaseError(
                "Cannot approve order without a cost center. Create one first."
            )

    def _register_purchase_on_approval(self, order_id: int) -> None:
        """Business rule: approving an order creates the purchase automatically."""
        existing = self.purchase_repo.list(filters={"id_pedido": order_id})
        if existing:
            return

        items = self.item_repo.list(filters={"id_pedido": order_id})
        centers = self.lookup_repo.list_cost_centers()
        order = self._get_order_model(order_id)
        assert order is not None and items and centers

        total = sum(float(i.quantidade) * float(i.valor_unitario) for i in items)
        try:
            record = self.purchase_repo.create(
                {
                    "id_pedido": order_id,
                    "id_centro_custo": centers[0].id_centro_custo,
                    "valor_total": total,
                    "data_compra": order.data_pedido or date.today(),
                }
            )
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not register purchase. Check that id_centro_custo exists."
            ) from exc
        self._request_stock_entry(record.id_compra)

    def delete_order(self, order_id: int) -> bool:
        if self.order_repo.get_by_id(order_id) is None:
            return False
        for purchase in self.purchase_repo.list(filters={"id_pedido": order_id}):
            self.purchase_repo.delete(purchase.id_compra)
        for item in self.item_repo.list(filters={"id_pedido": order_id}):
            self.item_repo.delete(item.id_item)
        return self.order_repo.delete(order_id)

    # --- Order items (always nested under an order) ---

    def add_item(
        self, order_id: int, payload: OrderItemCreateSchema
    ) -> OrderItemReadSchema | None:
        if self._ensure_order_editable(order_id) is None:
            return None
        data = payload.model_dump()
        data["id_pedido"] = order_id
        try:
            record = self.item_repo.create(data)
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not add item. Check that id_produto exists."
            ) from exc
        return self._load_item_read(record.id_item)

    def list_items(self, order_id: int) -> list[OrderItemReadSchema] | None:
        if self.order_repo.get_by_id(order_id) is None:
            return None
        return [
            self._to_item_read(item, nome, sigla)
            for item, nome, sigla in self.item_repo.list_with_product_labels(order_id)
        ]

    def update_item(
        self,
        order_id: int,
        item_id: int,
        payload: OrderItemUpdateSchema,
    ) -> OrderItemReadSchema | None:
        if self._ensure_order_editable(order_id) is None:
            return None
        item = self.item_repo.get_by_id(item_id)
        if item is None or item.id_pedido != order_id:
            return None
        record = self.item_repo.update(item_id, payload.model_dump(exclude_unset=True))
        if record is None:
            return None
        return self._load_item_read(item_id)

    def delete_item(self, order_id: int, item_id: int) -> bool:
        if self._ensure_order_editable(order_id) is None:
            return False
        item = self.item_repo.get_by_id(item_id)
        if item is None or item.id_pedido != order_id:
            return False
        siblings = self.item_repo.list(filters={"id_pedido": order_id})
        if len(siblings) <= 1:
            raise PurchaseError("An order must keep at least one item")
        return self.item_repo.delete(item_id)

    # --- Purchases ---

    def register_purchase(self, payload: PurchaseCreateSchema) -> PurchaseReadSchema | None:
        order = self._get_order_model(payload.id_pedido)
        if order is None:
            return None

        if order.status not in _PURCHASE_ALLOWED_STATUSES:
            raise PurchaseError(
                "Purchase can only be registered when the order status is APROVADO"
            )

        items = self.item_repo.list(filters={"id_pedido": payload.id_pedido})
        if not items:
            raise PurchaseError("An order without items cannot generate a purchase")

        try:
            record = self.purchase_repo.create(payload.model_dump())
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not register purchase. Check that id_centro_custo exists."
            ) from exc
        # Accounts payable / finance: integrate later. Purchase already records the acquisition.
        # Stock entry: inventory hook (no-op until implemented).
        self._request_stock_entry(record.id_compra)
        return PurchaseReadSchema.model_validate(record)

    def list_purchases(self) -> list[PurchaseReadSchema]:
        return [PurchaseReadSchema.model_validate(r) for r in self.purchase_repo.list()]

    def get_purchase(self, purchase_id: int) -> PurchaseReadSchema | None:
        record = self.purchase_repo.get_by_id(purchase_id)
        if record is None:
            return None
        return PurchaseReadSchema.model_validate(record)

    def update_purchase(
        self, purchase_id: int, payload: PurchaseUpdateSchema
    ) -> PurchaseReadSchema | None:
        record = self.purchase_repo.update(
            purchase_id, payload.model_dump(exclude_unset=True)
        )
        if record is None:
            return None
        return PurchaseReadSchema.model_validate(record)

    def delete_purchase(self, purchase_id: int) -> bool:
        return self.purchase_repo.delete(purchase_id)
