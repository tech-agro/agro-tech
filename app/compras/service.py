"""Purchase domain use cases."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from app.compras.enum import OrderStatus, PurchaseRequestStatus, PurchaseType, QuotationStatus
from app.compras.errors import PurchaseError
from app.compras.models.equipment_purchase_detail import EquipmentPurchaseDetailModel
from app.compras.models.order import OrderModel
from app.compras.models.order_item import OrderItemModel
from app.compras.models.purchase_request import PurchaseRequestModel
from app.compras.models.purchase_request_item import PurchaseRequestItemModel
from app.compras.models.quotation_item import QuotationItemModel
from app.compras.models.supplier_quotation import SupplierQuotationModel
from app.compras.repository import (
    EquipmentPurchaseDetailRepository,
    OrderItemRepository,
    OrderRepository,
    PurchaseInvoiceRepository,
    PurchaseLookupRepository,
    PurchaseRepository,
    PurchaseRequestItemRepository,
    PurchaseRequestRepository,
    QuotationItemRepository,
    SupplierQuotationRepository,
    SupplierRepository,
)
from app.compras.schemas.lookups import (
    CostCenterOptionSchema,
    FarmOptionSchema,
    MachineTypeOptionSchema,
    ProductOptionSchema,
    SupplierOptionSchema,
)
from app.compras.schemas.supplier import (
    SupplierCreateSchema,
    SupplierReadSchema,
    SupplierUpdateSchema,
)
from app.integrations.exceptions import (
    IntegrationHttpError,
    IntegrationNotFoundError,
    IntegrationValidationError,
)
from app.integrations.schemas import CompanyData
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
from app.compras.schemas.purchase_invoice import (
    PurchaseInvoiceCreateSchema,
    PurchaseInvoiceReadSchema,
    PurchaseInvoiceUpdateSchema,
)
from app.compras.schemas.purchase_request import (
    ConvertRequestToOrderSchema,
    PurchaseRequestCreateSchema,
    PurchaseRequestReadSchema,
    PurchaseRequestUpdateSchema,
)
from app.compras.schemas.purchase_request_item import (
    PurchaseRequestItemCreateSchema,
    PurchaseRequestItemReadSchema,
    PurchaseRequestItemUpdateSchema,
)
from app.compras.schemas.quotation_item import (
    QuotationItemCreateSchema,
    QuotationItemReadSchema,
)
from app.compras.schemas.supplier_quotation import (
    QuotationComparisonSchema,
    SupplierQuotationCreateSchema,
    SupplierQuotationReadSchema,
    SupplierQuotationUpdateSchema,
)
from app.core.database import get_session

if TYPE_CHECKING:
    from app.estoque.service import EstoqueService
    from app.financeiro.service import FinanceiroService
    from app.integrations.brasilapi import BrasilApiCnpjClient
    from app.manutencao.service import ManutencaoService

_EDITABLE_STATUSES = frozenset({OrderStatus.ABERTO})
_PURCHASE_ALLOWED_STATUSES = frozenset({OrderStatus.APROVADO})
_REQUEST_EDITABLE = frozenset({PurchaseRequestStatus.RASCUNHO})
_REQUEST_STATUS_TRANSITIONS: dict[
    PurchaseRequestStatus, frozenset[PurchaseRequestStatus]
] = {
    PurchaseRequestStatus.RASCUNHO: frozenset(
        {PurchaseRequestStatus.ENVIADA, PurchaseRequestStatus.CANCELADA}
    ),
    PurchaseRequestStatus.ENVIADA: frozenset(
        {
            PurchaseRequestStatus.APROVADA,
            PurchaseRequestStatus.REJEITADA,
            PurchaseRequestStatus.CANCELADA,
        }
    ),
}


class PurchaseService:
    """Orchestrates orders, items, and purchases. External integrations are hooks."""

    def __init__(
        self,
        order_repo: OrderRepository | None = None,
        item_repo: OrderItemRepository | None = None,
        purchase_repo: PurchaseRepository | None = None,
        lookup_repo: PurchaseLookupRepository | None = None,
        supplier_repo: SupplierRepository | None = None,
        request_repo: PurchaseRequestRepository | None = None,
        request_item_repo: PurchaseRequestItemRepository | None = None,
        quotation_repo: SupplierQuotationRepository | None = None,
        quotation_item_repo: QuotationItemRepository | None = None,
        invoice_repo: PurchaseInvoiceRepository | None = None,
        equipment_detail_repo: EquipmentPurchaseDetailRepository | None = None,
        inventory_service: EstoqueService | None = None,
        financeiro_service: FinanceiroService | None = None,
        manutencao_service: ManutencaoService | None = None,
        brasilapi_client: BrasilApiCnpjClient | None = None,
    ) -> None:
        self.order_repo = order_repo or OrderRepository()
        self.item_repo = item_repo or OrderItemRepository()
        self.purchase_repo = purchase_repo or PurchaseRepository()
        self.lookup_repo = lookup_repo or PurchaseLookupRepository()
        self.supplier_repo = supplier_repo or SupplierRepository()
        self.request_repo = request_repo or PurchaseRequestRepository()
        self.request_item_repo = request_item_repo or PurchaseRequestItemRepository()
        self.quotation_repo = quotation_repo or SupplierQuotationRepository()
        self.quotation_item_repo = quotation_item_repo or QuotationItemRepository()
        self.invoice_repo = invoice_repo or PurchaseInvoiceRepository()
        self.equipment_detail_repo = (
            equipment_detail_repo or EquipmentPurchaseDetailRepository()
        )
        self._inventory_service = inventory_service
        self._financeiro_service = financeiro_service
        self._manutencao_service = manutencao_service
        self._brasilapi_client = brasilapi_client

    def _brasilapi(self) -> BrasilApiCnpjClient:
        if self._brasilapi_client is None:
            from app.integrations.brasilapi import BrasilApiCnpjClient

            self._brasilapi_client = BrasilApiCnpjClient()
        return self._brasilapi_client

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

    def _financeiro(self) -> FinanceiroService:
        if self._financeiro_service is None:
            from app.financeiro.service import FinanceiroService
            self._financeiro_service = FinanceiroService()
        return self._financeiro_service

    def _manutencao(self) -> ManutencaoService:
        if self._manutencao_service is None:
            from app.manutencao.service import ManutencaoService
            self._manutencao_service = ManutencaoService()
        return self._manutencao_service

    def _request_conta_pagar(self, purchase_id: int, valor: Decimal, data_compra: date) -> None:
        """Accounts payable hook: registering a purchase creates a conta_pagar automatically."""
        self._financeiro().create_conta_pagar_from_compra(
            id_compra=purchase_id,
            valor=valor,
            vencimento=None,  # ajustar quando houver prazo de pagamento do fornecedor
        )

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

    def list_farm_options(self) -> list[FarmOptionSchema]:
        return [
            FarmOptionSchema.model_validate(row) for row in self.lookup_repo.list_farms()
        ]

    def list_machine_type_options(self) -> list[MachineTypeOptionSchema]:
        return [
            MachineTypeOptionSchema.model_validate(row)
            for row in self.lookup_repo.list_machine_types()
        ]

    # --- Suppliers ---

    def list_suppliers(self) -> list[SupplierReadSchema]:
        return self.supplier_repo.list()

    def get_supplier(self, supplier_id: int) -> SupplierReadSchema | None:
        return self.supplier_repo.get_by_id(supplier_id)

    def create_supplier(self, payload: SupplierCreateSchema) -> SupplierReadSchema:
        nome = payload.nome.strip()
        documento = payload.documento.strip()
        categoria = payload.categoria.strip() if payload.categoria else None
        if not nome or not documento:
            raise PurchaseError("Supplier name and document are required.")
        if self.supplier_repo.get_by_documento(documento) is not None:
            raise PurchaseError("A person with this document already exists.")
        try:
            return self.supplier_repo.create(
                nome=nome, documento=documento, categoria=categoria
            )
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not create supplier. Check that the document is unique."
            ) from exc

    def update_supplier(
        self, supplier_id: int, payload: SupplierUpdateSchema
    ) -> SupplierReadSchema | None:
        data = payload.model_dump(exclude_unset=True)
        if not data:
            return self.supplier_repo.get_by_id(supplier_id)

        nome = data["nome"].strip() if "nome" in data and data["nome"] is not None else None
        documento = (
            data["documento"].strip()
            if "documento" in data and data["documento"] is not None
            else None
        )
        update_categoria = "categoria" in data
        categoria = None
        if update_categoria:
            raw = data.get("categoria")
            categoria = raw.strip() if isinstance(raw, str) and raw.strip() else None

        if documento is not None:
            existing = self.supplier_repo.get_by_documento(documento)
            if existing is not None and existing.id_fornecedor != supplier_id:
                raise PurchaseError("A person with this document already exists.")

        try:
            return self.supplier_repo.update(
                supplier_id,
                nome=nome,
                documento=documento,
                categoria=categoria,
                update_categoria=update_categoria,
            )
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not update supplier. Check that the document is unique."
            ) from exc

    def delete_supplier(self, supplier_id: int) -> bool:
        if self.supplier_repo.get_by_id(supplier_id) is None:
            return False
        try:
            return self.supplier_repo.delete(supplier_id)
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not delete supplier: there are linked records."
            ) from exc

    def lookup_empresa_por_cnpj(self, cnpj: str) -> CompanyData:
        """Fetch company data from BrasilAPI for supplier form autofill."""
        try:
            return self._brasilapi().fetch(cnpj)
        except IntegrationNotFoundError as exc:
            raise PurchaseError(str(exc.message)) from exc
        except IntegrationValidationError as exc:
            raise PurchaseError(str(exc.message)) from exc
        except IntegrationHttpError as exc:
            raise PurchaseError(
                "Could not query CNPJ on BrasilAPI. Try again."
            ) from exc

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
            self.register_equipment_from_order(order_id)

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
        self._request_conta_pagar(record.id_compra, Decimal(str(total)), order.data_pedido or date.today())

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
        # Accounts payable / finance: finance
        # Stock entry: inventory hook (no-op).
        self._request_stock_entry(record.id_compra)
        self._request_conta_pagar(record.id_compra, Decimal(str(payload.valor_total)), payload.data_compra or date.today())
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

    # --- Purchase requests (solicitacao de compra) ---
    # Status flow: RASCUNHO -> ENVIADA -> APROVADA|REJEITADA; CANCELADA from RASCUNHO/ENVIADA.

    @staticmethod
    def _validate_equipment_fields(
        tipo_compra: PurchaseType,
        id_tipo_maquina: int | None,
        id_fazenda: int | None,
    ) -> None:
        if tipo_compra != PurchaseType.EQUIPAMENTO:
            return
        if id_tipo_maquina is None or id_fazenda is None:
            raise PurchaseError(
                "Equipment requests require machine type and farm."
            )

    def _get_request_model(self, request_id: int) -> PurchaseRequestModel | None:
        return self.request_repo.get_by_id(request_id)

    def _ensure_request_editable(self, request_id: int) -> PurchaseRequestModel | None:
        request = self._get_request_model(request_id)
        if request is None:
            return None
        if request.status not in _REQUEST_EDITABLE:
            raise PurchaseError(
                f"Request in status {request.status.value} does not allow item changes"
            )
        return request

    def _validate_request_status_transition(
        self,
        current: PurchaseRequestStatus,
        new: PurchaseRequestStatus,
    ) -> None:
        if new == current:
            return
        allowed = _REQUEST_STATUS_TRANSITIONS.get(current, frozenset())
        if new not in allowed:
            raise PurchaseError(
                f"Cannot transition request from {current.value} to {new.value}"
            )

    @staticmethod
    def _to_request_read(
        request: PurchaseRequestModel, id_pedido: int | None = None
    ) -> PurchaseRequestReadSchema:
        data = PurchaseRequestReadSchema.model_validate(request).model_dump()
        data["id_pedido"] = id_pedido
        return PurchaseRequestReadSchema.model_validate(data)

    def _load_request_read(self, request_id: int) -> PurchaseRequestReadSchema | None:
        request = self._get_request_model(request_id)
        if request is None:
            return None
        linked = self.order_repo.get_by_solicitacao(request_id)
        return self._to_request_read(request, linked.id_pedido if linked else None)

    def create_request(self, payload: PurchaseRequestCreateSchema) -> PurchaseRequestReadSchema:
        self._validate_equipment_fields(
            payload.tipo_compra, payload.id_tipo_maquina, payload.id_fazenda
        )
        header = payload.model_dump(exclude={"itens"})
        if header.get("data_solicitacao") is None:
            header["data_solicitacao"] = date.today()
        try:
            with get_session() as session:
                request = PurchaseRequestModel(**header)
                session.add(request)
                session.flush()
                request_id = request.id_solicitacao
                for item in payload.itens:
                    session.add(
                        PurchaseRequestItemModel(
                            id_solicitacao=request_id, **item.model_dump()
                        )
                    )
                session.flush()
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not create request. Check that id_produto exists."
            ) from exc
        loaded = self._load_request_read(request_id)
        assert loaded is not None
        return loaded

    def list_requests(self) -> list[PurchaseRequestReadSchema]:
        return [
            self._to_request_read(
                request,
                (linked.id_pedido if (linked := self.order_repo.get_by_solicitacao(request.id_solicitacao)) else None),
            )
            for request in self.request_repo.list()
        ]

    def get_request(self, request_id: int) -> PurchaseRequestReadSchema | None:
        return self._load_request_read(request_id)

    def update_request(
        self, request_id: int, payload: PurchaseRequestUpdateSchema
    ) -> PurchaseRequestReadSchema | None:
        previous = self._get_request_model(request_id)
        if previous is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        new_status = data.get("status")
        if new_status is not None:
            self._validate_request_status_transition(previous.status, new_status)
        tipo = data.get("tipo_compra", previous.tipo_compra)
        self._validate_equipment_fields(
            tipo,
            data.get("id_tipo_maquina", previous.id_tipo_maquina),
            data.get("id_fazenda", previous.id_fazenda),
        )
        if previous.status not in _REQUEST_EDITABLE and data.keys() - {"status"}:
            raise PurchaseError("Only status can be changed after the request is sent")
        record = self.request_repo.update(request_id, data)
        if record is None:
            return None
        return self._load_request_read(request_id)

    def delete_request(self, request_id: int) -> bool:
        request = self._get_request_model(request_id)
        if request is None:
            return False
        if self.order_repo.get_by_solicitacao(request_id) is not None:
            raise PurchaseError("Cannot delete a request that already generated an order")
        for item in self.request_item_repo.list(filters={"id_solicitacao": request_id}):
            self.request_item_repo.delete(item.id_item)
        for quotation in self.quotation_repo.list(filters={"id_solicitacao": request_id}):
            for q_item in self.quotation_item_repo.list(
                filters={"id_cotacao": quotation.id_cotacao}
            ):
                self.quotation_item_repo.delete(q_item.id_item_cotacao)
            self.quotation_repo.delete(quotation.id_cotacao)
        return self.request_repo.delete(request_id)

    def add_request_item(
        self, request_id: int, payload: PurchaseRequestItemCreateSchema
    ) -> PurchaseRequestItemReadSchema | None:
        if self._ensure_request_editable(request_id) is None:
            return None
        data = payload.model_dump()
        data["id_solicitacao"] = request_id
        try:
            record = self.request_item_repo.create(data)
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not add request item. Check that id_produto exists."
            ) from exc
        return self._load_request_item_read(record.id_item)

    def _load_request_item_read(self, item_id: int) -> PurchaseRequestItemReadSchema | None:
        item = self.request_item_repo.get_by_id(item_id)
        if item is None:
            return None
        rows = self.request_item_repo.list_with_product_labels(item.id_solicitacao)
        for loaded, nome, sigla in rows:
            if loaded.id_item == item_id:
                data = PurchaseRequestItemReadSchema.model_validate(loaded).model_dump()
                data["produto_nome"] = nome
                data["unidade_sigla"] = sigla
                return PurchaseRequestItemReadSchema.model_validate(data)
        return None

    def list_request_items(
        self, request_id: int
    ) -> list[PurchaseRequestItemReadSchema] | None:
        if self.request_repo.get_by_id(request_id) is None:
            return None
        return [
            PurchaseRequestItemReadSchema.model_validate(
                {
                    **PurchaseRequestItemReadSchema.model_validate(item).model_dump(),
                    "produto_nome": nome,
                    "unidade_sigla": sigla,
                }
            )
            for item, nome, sigla in self.request_item_repo.list_with_product_labels(
                request_id
            )
        ]

    def update_request_item(
        self,
        request_id: int,
        item_id: int,
        payload: PurchaseRequestItemUpdateSchema,
    ) -> PurchaseRequestItemReadSchema | None:
        if self._ensure_request_editable(request_id) is None:
            return None
        item = self.request_item_repo.get_by_id(item_id)
        if item is None or item.id_solicitacao != request_id:
            return None
        record = self.request_item_repo.update(
            item_id, payload.model_dump(exclude_unset=True)
        )
        if record is None:
            return None
        return self._load_request_item_read(item_id)

    def delete_request_item(self, request_id: int, item_id: int) -> bool:
        if self._ensure_request_editable(request_id) is None:
            return False
        item = self.request_item_repo.get_by_id(item_id)
        if item is None or item.id_solicitacao != request_id:
            return False
        siblings = self.request_item_repo.list(filters={"id_solicitacao": request_id})
        if len(siblings) <= 1:
            raise PurchaseError("A request must keep at least one item")
        return self.request_item_repo.delete(item_id)

    def convert_request_to_order(
        self, request_id: int, payload: ConvertRequestToOrderSchema
    ) -> OrderReadSchema | None:
        request = self._get_request_model(request_id)
        if request is None:
            return None
        if request.status != PurchaseRequestStatus.APROVADA:
            raise PurchaseError("Only approved requests can generate an order")
        if self.order_repo.get_by_solicitacao(request_id) is not None:
            raise PurchaseError("This request already generated an order")
        items = self.request_item_repo.list(filters={"id_solicitacao": request_id})
        if not items:
            raise PurchaseError("A request without items cannot generate an order")
        prices = payload.item_prices
        try:
            with get_session() as session:
                order = OrderModel(
                    id_fornecedor=payload.id_fornecedor,
                    data_pedido=date.today(),
                    status=OrderStatus.ABERTO,
                    id_solicitacao=request_id,
                    tipo_compra=request.tipo_compra,
                )
                session.add(order)
                session.flush()
                order_id = order.id_pedido
                for item in items:
                    unit_price = prices.get(item.id_item)
                    if unit_price is None:
                        raise PurchaseError(
                            f"Missing unit price for request item {item.id_item}"
                        )
                    session.add(
                        OrderItemModel(
                            id_pedido=order_id,
                            id_produto=item.id_produto,
                            quantidade=item.quantidade,
                            valor_unitario=unit_price,
                        )
                    )
                if request.tipo_compra == PurchaseType.EQUIPAMENTO:
                    session.add(
                        EquipmentPurchaseDetailModel(
                            id_pedido=order_id,
                            id_tipo_maquina=request.id_tipo_maquina,
                            patrimonio=request.patrimonio,
                            id_fazenda=request.id_fazenda,
                        )
                    )
                session.flush()
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not convert request to order. Check supplier and products."
            ) from exc
        loaded = self._load_order_read(order_id)
        assert loaded is not None
        return loaded

    # --- Supplier quotations ---

    @staticmethod
    def _to_quotation_read(
        quotation, fornecedor_nome: str | None
    ) -> SupplierQuotationReadSchema:
        data = SupplierQuotationReadSchema.model_validate(quotation).model_dump()
        data["fornecedor_nome"] = fornecedor_nome
        return SupplierQuotationReadSchema.model_validate(data)

    def create_quotation(
        self, request_id: int, payload: SupplierQuotationCreateSchema
    ) -> SupplierQuotationReadSchema | None:
        request = self._get_request_model(request_id)
        if request is None:
            return None
        if request.status != PurchaseRequestStatus.APROVADA:
            raise PurchaseError("Quotations require an approved request")
        header = payload.model_dump(exclude={"itens"})
        header["id_solicitacao"] = request_id
        try:
            with get_session() as session:
                quotation = SupplierQuotationModel(**header)
                session.add(quotation)
                session.flush()
                quotation_id = quotation.id_cotacao
                for item in payload.itens:
                    session.add(
                        QuotationItemModel(id_cotacao=quotation_id, **item.model_dump())
                    )
                session.flush()
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not create quotation. Check supplier and products."
            ) from exc
        rows = self.quotation_repo.list_with_supplier_name(request_id)
        for q, nome in rows:
            if q.id_cotacao == quotation_id:
                return self._to_quotation_read(q, nome)
        return None

    def list_quotations(
        self, request_id: int
    ) -> list[SupplierQuotationReadSchema] | None:
        if self.request_repo.get_by_id(request_id) is None:
            return None
        return [
            self._to_quotation_read(q, nome)
            for q, nome in self.quotation_repo.list_with_supplier_name(request_id)
        ]

    def list_quotation_items(
        self, quotation_id: int
    ) -> list[QuotationItemReadSchema] | None:
        if self.quotation_repo.get_by_id(quotation_id) is None:
            return None
        return [
            QuotationItemReadSchema.model_validate(
                {**QuotationItemReadSchema.model_validate(item).model_dump(), "produto_nome": nome}
            )
            for item, nome in self.quotation_item_repo.list_with_product_labels(
                quotation_id
            )
        ]

    def get_quotation_comparison(
        self, request_id: int
    ) -> QuotationComparisonSchema | None:
        if self.request_repo.get_by_id(request_id) is None:
            return None
        request_items = self.list_request_items(request_id) or []
        produtos = [
            {
                "id_produto": item.id_produto,
                "produto_nome": item.produto_nome,
                "quantidade": item.quantidade,
            }
            for item in request_items
        ]
        cotacoes = self.list_quotations(request_id) or []
        return QuotationComparisonSchema(
            id_solicitacao=request_id,
            produtos=produtos,
            cotacoes=cotacoes,
        )

    def select_winning_quotation(self, quotation_id: int) -> OrderReadSchema | None:
        quotation = self.quotation_repo.get_by_id(quotation_id)
        if quotation is None:
            return None
        request = self._get_request_model(quotation.id_solicitacao)
        if request is None:
            return None
        if request.status != PurchaseRequestStatus.APROVADA:
            raise PurchaseError("Winning quotation requires an approved request")
        for other in self.quotation_repo.list(
            filters={"id_solicitacao": quotation.id_solicitacao}
        ):
            if other.id_cotacao == quotation_id:
                self.quotation_repo.update(
                    other.id_cotacao, {"status": QuotationStatus.VENCEDORA}
                )
            elif other.status == QuotationStatus.VENCEDORA:
                self.quotation_repo.update(
                    other.id_cotacao, {"status": QuotationStatus.DESCARTADA}
                )
            else:
                self.quotation_repo.update(
                    other.id_cotacao, {"status": QuotationStatus.DESCARTADA}
                )
        request_items = self.request_item_repo.list(
            filters={"id_solicitacao": quotation.id_solicitacao}
        )
        q_items = self.quotation_item_repo.list(filters={"id_cotacao": quotation_id})
        price_by_product = {item.id_produto: float(item.preco_unitario) for item in q_items}
        item_prices: dict[int, float] = {}
        for req_item in request_items:
            price = price_by_product.get(req_item.id_produto)
            if price is None:
                raise PurchaseError(
                    f"Quotation missing price for product {req_item.id_produto}"
                )
            item_prices[req_item.id_item] = price
        return self.convert_request_to_order(
            quotation.id_solicitacao,
            ConvertRequestToOrderSchema(
                id_fornecedor=quotation.id_fornecedor,
                item_prices=item_prices,
            ),
        )

    def delete_quotation(self, request_id: int, quotation_id: int) -> bool:
        quotation = self.quotation_repo.get_by_id(quotation_id)
        if quotation is None or quotation.id_solicitacao != request_id:
            return False
        if quotation.status == QuotationStatus.VENCEDORA:
            raise PurchaseError("Cannot delete the winning quotation")
        for item in self.quotation_item_repo.list(filters={"id_cotacao": quotation_id}):
            self.quotation_item_repo.delete(item.id_item_cotacao)
        return self.quotation_repo.delete(quotation_id)

    # --- Purchase invoices (nota fiscal) ---

    def create_invoice(
        self, order_id: int, payload: PurchaseInvoiceCreateSchema
    ) -> PurchaseInvoiceReadSchema | None:
        order = self._get_order_model(order_id)
        if order is None:
            return None
        if payload.valor_total <= 0:
            raise PurchaseError("Invoice total must be greater than zero")
        data = payload.model_dump()
        data["id_pedido"] = order_id
        data["id_fornecedor"] = order.id_fornecedor
        try:
            record = self.invoice_repo.create(data)
        except IntegrityError as exc:
            raise PurchaseError(
                "Could not create invoice. Check number, series and supplier uniqueness."
            ) from exc
        return PurchaseInvoiceReadSchema.model_validate(record)

    def list_invoices(self, order_id: int) -> list[PurchaseInvoiceReadSchema] | None:
        if self.order_repo.get_by_id(order_id) is None:
            return None
        return [
            PurchaseInvoiceReadSchema.model_validate(row)
            for row in self.invoice_repo.list(filters={"id_pedido": order_id})
        ]

    def get_invoice(self, invoice_id: int) -> PurchaseInvoiceReadSchema | None:
        record = self.invoice_repo.get_by_id(invoice_id)
        if record is None:
            return None
        return PurchaseInvoiceReadSchema.model_validate(record)

    def update_invoice(
        self, invoice_id: int, payload: PurchaseInvoiceUpdateSchema
    ) -> PurchaseInvoiceReadSchema | None:
        record = self.invoice_repo.update(
            invoice_id, payload.model_dump(exclude_unset=True)
        )
        if record is None:
            return None
        return PurchaseInvoiceReadSchema.model_validate(record)

    def delete_invoice(self, invoice_id: int) -> bool:
        return self.invoice_repo.delete(invoice_id)

    # --- Equipment purchase (compra de maquinas) ---

    def register_equipment_from_order(self, order_id: int) -> None:
        order = self._get_order_model(order_id)
        if order is None or order.tipo_compra != PurchaseType.EQUIPAMENTO:
            return
        if order.status != OrderStatus.APROVADO:
            return
        detail = self.equipment_detail_repo.get_by_id(order_id)
        if detail is None or detail.id_maquina is not None:
            return
        from app.manutencao.schemas.maquina import MaquinaCreateSchema

        machine_name = detail.patrimonio or f"Equipamento pedido #{order_id}"
        maquina = self._manutencao().create_maquina(
            MaquinaCreateSchema(
                id_tipo_maquina=detail.id_tipo_maquina,
                nome=machine_name,
                status="DISPONIVEL",
            ),
            id_fazenda=detail.id_fazenda,
        )
        self.equipment_detail_repo.update(order_id, {"id_maquina": maquina.id_maquina})
