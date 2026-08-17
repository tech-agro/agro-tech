"""HTTP adapter for the purchases domain (domain resources only)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.compras.errors import PurchaseError
from app.compras.schemas.lookups import (
    CostCenterOptionSchema,
    FarmOptionSchema,
    MachineTypeOptionSchema,
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
from app.compras.schemas.quotation_item import QuotationItemReadSchema
from app.compras.schemas.supplier_quotation import (
    QuotationComparisonSchema,
    SupplierQuotationCreateSchema,
    SupplierQuotationReadSchema,
)
from app.compras.schemas.purchase import (
    PurchaseCreateSchema,
    PurchaseReadSchema,
    PurchaseUpdateSchema,
)
from app.compras.schemas.supplier import (
    SupplierCreateSchema,
    SupplierReadSchema,
    SupplierUpdateSchema,
)
from app.compras.service import PurchaseService
from app.integrations.schemas import CompanyData


class PurchaseController:
    """Exposes Order and Purchase; items are nested under the order."""

    def __init__(self, service: PurchaseService | None = None) -> None:
        self.service = service or PurchaseService()
        self.router = APIRouter(prefix="/purchases", tags=["purchases"])
        self._register_routes()

    @staticmethod
    def _map_error(exc: PurchaseError) -> HTTPException:
        return HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    def _register_routes(self) -> None:
        # Shared-catalog lookups for the UI until catalog modules own these APIs.
        self.router.get("/lookups/products", response_model=list[ProductOptionSchema])(
            self.list_product_options
        )
        self.router.get("/lookups/suppliers", response_model=list[SupplierOptionSchema])(
            self.list_supplier_options
        )
        self.router.get(
            "/lookups/cost-centers", response_model=list[CostCenterOptionSchema]
        )(self.list_cost_center_options)
        self.router.get("/lookups/farms", response_model=list[FarmOptionSchema])(
            self.list_farm_options
        )
        self.router.get(
            "/lookups/machine-types", response_model=list[MachineTypeOptionSchema]
        )(self.list_machine_type_options)
        self.router.get("/cnpj/{cnpj}", response_model=CompanyData)(
            self.lookup_empresa_por_cnpj
        )

        self.router.post("/requests", response_model=PurchaseRequestReadSchema)(
            self.create_request
        )
        self.router.get("/requests", response_model=list[PurchaseRequestReadSchema])(
            self.list_requests
        )
        self.router.get(
            "/requests/{request_id}", response_model=PurchaseRequestReadSchema
        )(self.get_request)
        self.router.patch(
            "/requests/{request_id}", response_model=PurchaseRequestReadSchema
        )(self.update_request)
        self.router.delete(
            "/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_request)
        self.router.post(
            "/requests/{request_id}/items",
            response_model=PurchaseRequestItemReadSchema,
        )(self.add_request_item)
        self.router.get(
            "/requests/{request_id}/items",
            response_model=list[PurchaseRequestItemReadSchema],
        )(self.list_request_items)
        self.router.patch(
            "/requests/{request_id}/items/{item_id}",
            response_model=PurchaseRequestItemReadSchema,
        )(self.update_request_item)
        self.router.delete(
            "/requests/{request_id}/items/{item_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_request_item)
        self.router.post(
            "/requests/{request_id}/convert-to-order",
            response_model=OrderReadSchema,
        )(self.convert_request_to_order)
        self.router.get(
            "/requests/{request_id}/quotations/comparison",
            response_model=QuotationComparisonSchema,
        )(self.get_quotation_comparison)
        self.router.post(
            "/requests/{request_id}/quotations",
            response_model=SupplierQuotationReadSchema,
        )(self.create_quotation)
        self.router.get(
            "/requests/{request_id}/quotations",
            response_model=list[SupplierQuotationReadSchema],
        )(self.list_quotations)
        self.router.delete(
            "/requests/{request_id}/quotations/{quotation_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_quotation)
        self.router.get(
            "/quotations/{quotation_id}/items",
            response_model=list[QuotationItemReadSchema],
        )(self.list_quotation_items)
        self.router.post(
            "/quotations/{quotation_id}/select-winner",
            response_model=OrderReadSchema,
        )(self.select_winning_quotation)
        self.router.get(
            "/invoices/{invoice_id}", response_model=PurchaseInvoiceReadSchema
        )(self.get_invoice)
        self.router.patch(
            "/invoices/{invoice_id}", response_model=PurchaseInvoiceReadSchema
        )(self.update_invoice)
        self.router.delete(
            "/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_invoice)

        # Supplier CRUD (must be registered before /{purchase_id}).
        self.router.post("/suppliers", response_model=SupplierReadSchema)(
            self.create_supplier
        )
        self.router.get("/suppliers", response_model=list[SupplierReadSchema])(
            self.list_suppliers
        )
        self.router.get("/suppliers/{supplier_id}", response_model=SupplierReadSchema)(
            self.get_supplier
        )
        self.router.patch("/suppliers/{supplier_id}", response_model=SupplierReadSchema)(
            self.update_supplier
        )
        self.router.delete(
            "/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_supplier)

        self.router.post("/orders", response_model=OrderReadSchema)(self.create_order)
        self.router.get("/orders", response_model=list[OrderReadSchema])(self.list_orders)
        self.router.get("/orders/{order_id}", response_model=OrderReadSchema)(self.get_order)
        self.router.patch("/orders/{order_id}", response_model=OrderReadSchema)(
            self.update_order
        )
        self.router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)(
            self.delete_order
        )

        self.router.post(
            "/orders/{order_id}/items",
            response_model=OrderItemReadSchema,
        )(self.add_item)
        self.router.get(
            "/orders/{order_id}/items",
            response_model=list[OrderItemReadSchema],
        )(self.list_items)
        self.router.patch(
            "/orders/{order_id}/items/{item_id}",
            response_model=OrderItemReadSchema,
        )(self.update_item)
        self.router.delete(
            "/orders/{order_id}/items/{item_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_item)

        self.router.post(
            "/orders/{order_id}/invoices",
            response_model=PurchaseInvoiceReadSchema,
        )(self.create_invoice)
        self.router.get(
            "/orders/{order_id}/invoices",
            response_model=list[PurchaseInvoiceReadSchema],
        )(self.list_invoices)

        self.router.post("/", response_model=PurchaseReadSchema)(self.register_purchase)
        self.router.get("/", response_model=list[PurchaseReadSchema])(self.list_purchases)
        self.router.get("/{purchase_id}", response_model=PurchaseReadSchema)(
            self.get_purchase
        )
        self.router.patch("/{purchase_id}", response_model=PurchaseReadSchema)(
            self.update_purchase
        )
        self.router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)(
            self.delete_purchase
        )

    def list_product_options(self) -> list[ProductOptionSchema]:
        return self.service.list_product_options()

    def list_supplier_options(self) -> list[SupplierOptionSchema]:
        return self.service.list_supplier_options()

    def list_cost_center_options(self) -> list[CostCenterOptionSchema]:
        return self.service.list_cost_center_options()

    def list_farm_options(self) -> list[FarmOptionSchema]:
        return self.service.list_farm_options()

    def list_machine_type_options(self) -> list[MachineTypeOptionSchema]:
        return self.service.list_machine_type_options()

    def lookup_empresa_por_cnpj(self, cnpj: str) -> CompanyData:
        try:
            return self.service.lookup_empresa_por_cnpj(cnpj)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc

    def create_supplier(self, payload: SupplierCreateSchema) -> SupplierReadSchema:
        try:
            return self.service.create_supplier(payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc

    def list_suppliers(self) -> list[SupplierReadSchema]:
        return self.service.list_suppliers()

    def get_supplier(self, supplier_id: int) -> SupplierReadSchema:
        supplier = self.service.get_supplier(supplier_id)
        if supplier is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
        return supplier

    def update_supplier(
        self, supplier_id: int, payload: SupplierUpdateSchema
    ) -> SupplierReadSchema:
        try:
            supplier = self.service.update_supplier(supplier_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if supplier is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
        return supplier

    def delete_supplier(self, supplier_id: int) -> None:
        try:
            ok = self.service.delete_supplier(supplier_id)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")

    def create_order(self, payload: OrderCreateSchema) -> OrderReadSchema:
        try:
            return self.service.create_order(payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc

    def list_orders(self) -> list[OrderReadSchema]:
        return self.service.list_orders()

    def get_order(self, order_id: int) -> OrderReadSchema:
        order = self.service.get_order(order_id)
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return order

    def update_order(self, order_id: int, payload: OrderUpdateSchema) -> OrderReadSchema:
        try:
            order = self.service.update_order(order_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return order

    def delete_order(self, order_id: int) -> None:
        if not self.service.delete_order(order_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")

    def add_item(
        self, order_id: int, payload: OrderItemCreateSchema
    ) -> OrderItemReadSchema:
        try:
            item = self.service.add_item(order_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return item

    def list_items(self, order_id: int) -> list[OrderItemReadSchema]:
        items = self.service.list_items(order_id)
        if items is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return items

    def update_item(
        self,
        order_id: int,
        item_id: int,
        payload: OrderItemUpdateSchema,
    ) -> OrderItemReadSchema:
        try:
            item = self.service.update_item(order_id, item_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order item not found")
        return item

    def delete_item(self, order_id: int, item_id: int) -> None:
        try:
            ok = self.service.delete_item(order_id, item_id)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order item not found")

    def register_purchase(self, payload: PurchaseCreateSchema) -> PurchaseReadSchema:
        try:
            purchase = self.service.register_purchase(payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if purchase is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return purchase

    def list_purchases(self) -> list[PurchaseReadSchema]:
        return self.service.list_purchases()

    def get_purchase(self, purchase_id: int) -> PurchaseReadSchema:
        purchase = self.service.get_purchase(purchase_id)
        if purchase is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase not found")
        return purchase

    def update_purchase(
        self, purchase_id: int, payload: PurchaseUpdateSchema
    ) -> PurchaseReadSchema:
        purchase = self.service.update_purchase(purchase_id, payload)
        if purchase is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase not found")
        return purchase

    def delete_purchase(self, purchase_id: int) -> None:
        if not self.service.delete_purchase(purchase_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase not found")

    def create_request(self, payload: PurchaseRequestCreateSchema) -> PurchaseRequestReadSchema:
        try:
            return self.service.create_request(payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc

    def list_requests(self) -> list[PurchaseRequestReadSchema]:
        return self.service.list_requests()

    def get_request(self, request_id: int) -> PurchaseRequestReadSchema:
        request = self.service.get_request(request_id)
        if request is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return request

    def update_request(
        self, request_id: int, payload: PurchaseRequestUpdateSchema
    ) -> PurchaseRequestReadSchema:
        try:
            request = self.service.update_request(request_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if request is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return request

    def delete_request(self, request_id: int) -> None:
        try:
            ok = self.service.delete_request(request_id)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")

    def add_request_item(
        self, request_id: int, payload: PurchaseRequestItemCreateSchema
    ) -> PurchaseRequestItemReadSchema:
        try:
            item = self.service.add_request_item(request_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return item

    def list_request_items(
        self, request_id: int
    ) -> list[PurchaseRequestItemReadSchema]:
        items = self.service.list_request_items(request_id)
        if items is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return items

    def update_request_item(
        self,
        request_id: int,
        item_id: int,
        payload: PurchaseRequestItemUpdateSchema,
    ) -> PurchaseRequestItemReadSchema:
        try:
            item = self.service.update_request_item(request_id, item_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request item not found")
        return item

    def delete_request_item(self, request_id: int, item_id: int) -> None:
        try:
            ok = self.service.delete_request_item(request_id, item_id)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request item not found")

    def convert_request_to_order(
        self, request_id: int, payload: ConvertRequestToOrderSchema
    ) -> OrderReadSchema:
        try:
            order = self.service.convert_request_to_order(request_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return order

    def create_quotation(
        self, request_id: int, payload: SupplierQuotationCreateSchema
    ) -> SupplierQuotationReadSchema:
        try:
            quotation = self.service.create_quotation(request_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if quotation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return quotation

    def list_quotations(self, request_id: int) -> list[SupplierQuotationReadSchema]:
        quotations = self.service.list_quotations(request_id)
        if quotations is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return quotations

    def list_quotation_items(self, quotation_id: int) -> list[QuotationItemReadSchema]:
        items = self.service.list_quotation_items(quotation_id)
        if items is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Quotation not found")
        return items

    def get_quotation_comparison(self, request_id: int) -> QuotationComparisonSchema:
        comparison = self.service.get_quotation_comparison(request_id)
        if comparison is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Purchase request not found")
        return comparison

    def select_winning_quotation(self, quotation_id: int) -> OrderReadSchema:
        try:
            order = self.service.select_winning_quotation(quotation_id)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if order is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Quotation not found")
        return order

    def delete_quotation(self, request_id: int, quotation_id: int) -> None:
        try:
            ok = self.service.delete_quotation(request_id, quotation_id)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Quotation not found")

    def create_invoice(
        self, order_id: int, payload: PurchaseInvoiceCreateSchema
    ) -> PurchaseInvoiceReadSchema:
        try:
            invoice = self.service.create_invoice(order_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if invoice is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return invoice

    def list_invoices(self, order_id: int) -> list[PurchaseInvoiceReadSchema]:
        invoices = self.service.list_invoices(order_id)
        if invoices is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
        return invoices

    def get_invoice(self, invoice_id: int) -> PurchaseInvoiceReadSchema:
        invoice = self.service.get_invoice(invoice_id)
        if invoice is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
        return invoice

    def update_invoice(
        self, invoice_id: int, payload: PurchaseInvoiceUpdateSchema
    ) -> PurchaseInvoiceReadSchema:
        try:
            invoice = self.service.update_invoice(invoice_id, payload)
        except PurchaseError as exc:
            raise self._map_error(exc) from exc
        if invoice is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")
        return invoice

    def delete_invoice(self, invoice_id: int) -> None:
        if not self.service.delete_invoice(invoice_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Invoice not found")


purchase_controller = PurchaseController()
router = purchase_controller.router
