"""HTTP client for the purchases Streamlit UI → FastAPI."""

from __future__ import annotations

from datetime import date

import requests

from app.compras.enum import OrderStatus
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
from app.compras.schemas.supplier import (
    SupplierCreateSchema,
    SupplierReadSchema,
    SupplierUpdateSchema,
)
from app.core.config import settings
from app.integrations.schemas import CompanyData


# API returns English details; Streamlit must show Portuguese to the user.
_API_DETAIL_TO_PT: tuple[tuple[str, str], ...] = (
    ("id_fornecedor and id_produto exist", "Verifique se o fornecedor e os produtos existem."),
    ("id_fornecedor exists", "Verifique se o ID do fornecedor existe."),
    ("id_produto exists", "Verifique se o ID do produto existe."),
    ("id_centro_custo exists", "Verifique se o ID do centro de custo existe."),
    ("does not allow item changes", "Este pedido nao permite alterar itens no status atual."),
    ("order status is APROVADO", "So e possivel registrar compra com pedido Aprovado."),
    ("without items", "Pedido sem itens nao pode gerar compra."),
    ("without a cost center", "Nao ha centro de custo cadastrado para registrar a compra."),
    ("at least one item", "O pedido deve manter pelo menos um item."),
    ("Order not found", "Pedido nao encontrado."),
    ("Order item not found", "Item do pedido nao encontrado."),
    ("Purchase not found", "Compra nao encontrada."),
    ("Supplier not found", "Fornecedor nao encontrado."),
    ("document already exists", "Ja existe uma pessoa com este documento."),
    ("document is unique", "Ja existe uma pessoa com este documento."),
    ("name and document are required", "Informe nome e documento do fornecedor."),
    ("linked records", "Nao foi possivel excluir: ha registros vinculados."),
    ("CNPJ invalido", "Informe um CNPJ valido (14 digitos)."),
    ("nao encontrado na BrasilAPI", "CNPJ nao encontrado."),
    ("Could not query CNPJ on BrasilAPI", "Nao foi possivel consultar o CNPJ. Tente novamente."),
    ("foreign key", "Nao foi possivel excluir: ha registros vinculados."),
)


def _to_user_message(detail: str, status_code: int | None) -> str:
    lowered = detail.lower()
    for needle, portuguese in _API_DETAIL_TO_PT:
        if needle.lower() in lowered:
            return portuguese
    if status_code == 404:
        return "Registro nao encontrado."
    if status_code == 400:
        return "Nao foi possivel concluir a operacao. Verifique os dados informados."
    if status_code == 422:
        return "Dados invalidos. Revise o formulario."
    return "Falha na comunicacao com a API."


class PurchasesApiError(Exception):
    """Raised when the purchases API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message  # English detail from API (for logs/debug)
        self.status_code = status_code
        self.user_message = _to_user_message(message, status_code)  # Portuguese UI
        super().__init__(message)


class PurchasesClient:
    def __init__(self, base_url: str | None = None, timeout: float = 15) -> None:
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _raise_for_api(self, response: requests.Response) -> None:
        if response.ok:
            return
        detail: str
        try:
            payload = response.json()
            detail = str(payload.get("detail", response.text))
        except Exception:
            detail = response.text or response.reason
        raise PurchasesApiError(detail, status_code=response.status_code)

    # --- Lookups ---

    def list_products(self) -> list[ProductOptionSchema]:
        response = requests.get(
            self._url("/purchases/lookups/products"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [ProductOptionSchema.model_validate(item) for item in response.json()]

    def list_suppliers(self) -> list[SupplierOptionSchema]:
        response = requests.get(
            self._url("/purchases/lookups/suppliers"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [SupplierOptionSchema.model_validate(item) for item in response.json()]

    def list_cost_centers(self) -> list[CostCenterOptionSchema]:
        response = requests.get(
            self._url("/purchases/lookups/cost-centers"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [CostCenterOptionSchema.model_validate(item) for item in response.json()]

    # --- Suppliers ---

    def list_suppliers_full(self) -> list[SupplierReadSchema]:
        response = requests.get(self._url("/purchases/suppliers"), timeout=self.timeout)
        self._raise_for_api(response)
        return [SupplierReadSchema.model_validate(item) for item in response.json()]

    def get_supplier(self, supplier_id: int) -> SupplierReadSchema:
        response = requests.get(
            self._url(f"/purchases/suppliers/{supplier_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return SupplierReadSchema.model_validate(response.json())

    def create_supplier(self, payload: SupplierCreateSchema) -> SupplierReadSchema:
        response = requests.post(
            self._url("/purchases/suppliers"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return SupplierReadSchema.model_validate(response.json())

    def update_supplier(
        self, supplier_id: int, payload: SupplierUpdateSchema
    ) -> SupplierReadSchema:
        response = requests.patch(
            self._url(f"/purchases/suppliers/{supplier_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return SupplierReadSchema.model_validate(response.json())

    def delete_supplier(self, supplier_id: int) -> None:
        response = requests.delete(
            self._url(f"/purchases/suppliers/{supplier_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    def lookup_empresa_por_cnpj(self, cnpj: str) -> CompanyData:
        response = requests.get(
            self._url(f"/purchases/cnpj/{cnpj}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return CompanyData.model_validate(response.json())

    # --- Orders ---

    def list_orders(self) -> list[OrderReadSchema]:
        response = requests.get(self._url("/purchases/orders"), timeout=self.timeout)
        self._raise_for_api(response)
        return [OrderReadSchema.model_validate(item) for item in response.json()]

    def get_order(self, order_id: int) -> OrderReadSchema:
        response = requests.get(
            self._url(f"/purchases/orders/{order_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return OrderReadSchema.model_validate(response.json())

    def create_order(
        self,
        *,
        id_fornecedor: int,
        itens: list[OrderItemCreateSchema],
        data_pedido: date | None = None,
        status: OrderStatus = OrderStatus.ABERTO,
    ) -> OrderReadSchema:
        payload = OrderCreateSchema(
            id_fornecedor=id_fornecedor,
            data_pedido=data_pedido,
            status=status,
            itens=itens,
        )
        response = requests.post(
            self._url("/purchases/orders"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return OrderReadSchema.model_validate(response.json())

    def update_order(self, order_id: int, payload: OrderUpdateSchema) -> OrderReadSchema:
        response = requests.patch(
            self._url(f"/purchases/orders/{order_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return OrderReadSchema.model_validate(response.json())

    def delete_order(self, order_id: int) -> None:
        response = requests.delete(
            self._url(f"/purchases/orders/{order_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- Order items ---

    def list_items(self, order_id: int) -> list[OrderItemReadSchema]:
        response = requests.get(
            self._url(f"/purchases/orders/{order_id}/items"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [OrderItemReadSchema.model_validate(item) for item in response.json()]

    def add_item(
        self,
        order_id: int,
        *,
        id_produto: int,
        quantidade: float,
        valor_unitario: float,
    ) -> OrderItemReadSchema:
        payload = OrderItemCreateSchema(
            id_produto=id_produto,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
        )
        response = requests.post(
            self._url(f"/purchases/orders/{order_id}/items"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return OrderItemReadSchema.model_validate(response.json())

    def update_item(
        self,
        order_id: int,
        item_id: int,
        payload: OrderItemUpdateSchema,
    ) -> OrderItemReadSchema:
        response = requests.patch(
            self._url(f"/purchases/orders/{order_id}/items/{item_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return OrderItemReadSchema.model_validate(response.json())

    def delete_item(self, order_id: int, item_id: int) -> None:
        response = requests.delete(
            self._url(f"/purchases/orders/{order_id}/items/{item_id}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)

    # --- Purchases ---

    def list_purchases(self) -> list[PurchaseReadSchema]:
        response = requests.get(self._url("/purchases/"), timeout=self.timeout)
        self._raise_for_api(response)
        return [PurchaseReadSchema.model_validate(item) for item in response.json()]

    def register_purchase(
        self,
        *,
        id_pedido: int,
        id_centro_custo: int,
        valor_total: float,
        data_compra: date | None = None,
    ) -> PurchaseReadSchema:
        payload = PurchaseCreateSchema(
            id_pedido=id_pedido,
            id_centro_custo=id_centro_custo,
            valor_total=valor_total,
            data_compra=data_compra,
        )
        response = requests.post(
            self._url("/purchases/"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return PurchaseReadSchema.model_validate(response.json())

    def update_purchase(
        self, purchase_id: int, payload: PurchaseUpdateSchema
    ) -> PurchaseReadSchema:
        response = requests.patch(
            self._url(f"/purchases/{purchase_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return PurchaseReadSchema.model_validate(response.json())

    def delete_purchase(self, purchase_id: int) -> None:
        response = requests.delete(
            self._url(f"/purchases/{purchase_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
