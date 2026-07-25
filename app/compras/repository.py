"""Data access for the purchases domain."""

from __future__ import annotations

from sqlalchemy import select

from app.compras.models.order import OrderModel
from app.compras.models.order_item import OrderItemModel
from app.compras.models.purchase import PurchaseModel
from app.compras.models.refs import (
    CentroCustoRef,
    FornecedorRef,
    PessoaRef,
    ProdutoRef,
    UnidadeMedidaRef,
)
from app.compras.models.supplier_product import SupplierProductModel
from app.core.base_repository import BaseRepository
from app.core.database import get_session

# Register FK targets on SQLAlchemy metadata (shared tables owned elsewhere).
_ = (PessoaRef, FornecedorRef, UnidadeMedidaRef, ProdutoRef, CentroCustoRef)


class OrderRepository(BaseRepository[OrderModel]):
    model = OrderModel

    def list_with_supplier_name(self) -> list[tuple[OrderModel, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(OrderModel, PessoaRef.nome)
                .outerjoin(FornecedorRef, FornecedorRef.id_fornecedor == OrderModel.id_fornecedor)
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == FornecedorRef.id_pessoa)
                .order_by(OrderModel.id_pedido)
            ).all()
            result: list[tuple[OrderModel, str | None]] = []
            for order, nome in rows:
                session.expunge(order)
                result.append((order, nome))
            return result

    def get_with_supplier_name(
        self, order_id: int
    ) -> tuple[OrderModel, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(OrderModel, PessoaRef.nome)
                .outerjoin(FornecedorRef, FornecedorRef.id_fornecedor == OrderModel.id_fornecedor)
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == FornecedorRef.id_pessoa)
                .where(OrderModel.id_pedido == order_id)
            ).first()
            if row is None:
                return None
            order, nome = row
            session.expunge(order)
            return order, nome


class OrderItemRepository(BaseRepository[OrderItemModel]):
    model = OrderItemModel

    def list_with_product_labels(
        self, order_id: int
    ) -> list[tuple[OrderItemModel, str | None, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(OrderItemModel, ProdutoRef.nome, UnidadeMedidaRef.sigla)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == OrderItemModel.id_produto)
                .outerjoin(
                    UnidadeMedidaRef, UnidadeMedidaRef.id_unidade == ProdutoRef.id_unidade
                )
                .where(OrderItemModel.id_pedido == order_id)
                .order_by(OrderItemModel.id_item)
            ).all()
            result: list[tuple[OrderItemModel, str | None, str | None]] = []
            for item, nome, sigla in rows:
                session.expunge(item)
                result.append((item, nome, sigla))
            return result

    def get_with_product_labels(
        self, item_id: int
    ) -> tuple[OrderItemModel, str | None, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(OrderItemModel, ProdutoRef.nome, UnidadeMedidaRef.sigla)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == OrderItemModel.id_produto)
                .outerjoin(
                    UnidadeMedidaRef, UnidadeMedidaRef.id_unidade == ProdutoRef.id_unidade
                )
                .where(OrderItemModel.id_item == item_id)
            ).first()
            if row is None:
                return None
            item, nome, sigla = row
            session.expunge(item)
            return item, nome, sigla


class SupplierProductRepository(BaseRepository[SupplierProductModel]):
    """Auxiliary table: no controller; internal use when business rules need it."""

    model = SupplierProductModel


class PurchaseRepository(BaseRepository[PurchaseModel]):
    model = PurchaseModel


class PurchaseLookupRepository:
    """Read-only access to shared catalog tables for purchases UI labels."""

    def list_products(self) -> list[tuple[ProdutoRef, UnidadeMedidaRef]]:
        with get_session() as session:
            rows = session.execute(
                select(ProdutoRef, UnidadeMedidaRef)
                .join(UnidadeMedidaRef, UnidadeMedidaRef.id_unidade == ProdutoRef.id_unidade)
                .order_by(ProdutoRef.nome)
            ).all()
            result: list[tuple[ProdutoRef, UnidadeMedidaRef]] = []
            for produto, unidade in rows:
                session.expunge(produto)
                session.expunge(unidade)
                result.append((produto, unidade))
            return result

    def list_suppliers(self) -> list[tuple[FornecedorRef, str]]:
        with get_session() as session:
            rows = session.execute(
                select(FornecedorRef, PessoaRef.nome)
                .join(PessoaRef, PessoaRef.id_pessoa == FornecedorRef.id_pessoa)
                .order_by(PessoaRef.nome)
            ).all()
            result: list[tuple[FornecedorRef, str]] = []
            for fornecedor, nome in rows:
                session.expunge(fornecedor)
                result.append((fornecedor, nome))
            return result

    def list_cost_centers(self) -> list[CentroCustoRef]:
        with get_session() as session:
            rows = session.scalars(
                select(CentroCustoRef).order_by(CentroCustoRef.nome)
            ).all()
            for row in rows:
                session.expunge(row)
            return list(rows)
