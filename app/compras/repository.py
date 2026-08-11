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
from app.compras.schemas.supplier import SupplierReadSchema
from app.core.base_repository import BaseRepository
from app.core.database import get_session

# Register FK targets on SQLAlchemy metadata (shared tables owned elsewhere).
_ = (PessoaRef, FornecedorRef, UnidadeMedidaRef, ProdutoRef, CentroCustoRef)


def _supplier_read(
    fornecedor: FornecedorRef, pessoa: PessoaRef
) -> SupplierReadSchema:
    return SupplierReadSchema(
        id_fornecedor=fornecedor.id_fornecedor,
        id_pessoa=pessoa.id_pessoa,
        nome=pessoa.nome,
        documento=pessoa.documento,
        categoria=fornecedor.categoria,
    )


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
                .select_from(OrderItemModel)
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
                .select_from(OrderItemModel)
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


class SupplierRepository:
    """CRUD for fornecedor + pessoa (person row created with the supplier)."""

    def create(
        self, *, nome: str, documento: str, categoria: str | None
    ) -> SupplierReadSchema:
        with get_session() as session:
            pessoa = PessoaRef(nome=nome, documento=documento)
            session.add(pessoa)
            session.flush()
            fornecedor = FornecedorRef(id_pessoa=pessoa.id_pessoa, categoria=categoria)
            session.add(fornecedor)
            session.flush()
            return _supplier_read(fornecedor, pessoa)

    def list(self) -> list[SupplierReadSchema]:
        with get_session() as session:
            rows = session.execute(
                select(FornecedorRef, PessoaRef)
                .join(PessoaRef, PessoaRef.id_pessoa == FornecedorRef.id_pessoa)
                .order_by(PessoaRef.nome)
            ).all()
            return [_supplier_read(fornecedor, pessoa) for fornecedor, pessoa in rows]

    def get_by_id(self, supplier_id: int) -> SupplierReadSchema | None:
        with get_session() as session:
            row = session.execute(
                select(FornecedorRef, PessoaRef)
                .join(PessoaRef, PessoaRef.id_pessoa == FornecedorRef.id_pessoa)
                .where(FornecedorRef.id_fornecedor == supplier_id)
            ).first()
            if row is None:
                return None
            fornecedor, pessoa = row
            return _supplier_read(fornecedor, pessoa)

    def get_by_documento(self, documento: str) -> SupplierReadSchema | None:
        with get_session() as session:
            row = session.execute(
                select(FornecedorRef, PessoaRef)
                .join(PessoaRef, PessoaRef.id_pessoa == FornecedorRef.id_pessoa)
                .where(PessoaRef.documento == documento)
            ).first()
            if row is None:
                return None
            fornecedor, pessoa = row
            return _supplier_read(fornecedor, pessoa)

    def update(
        self,
        supplier_id: int,
        *,
        nome: str | None = None,
        documento: str | None = None,
        categoria: str | None = None,
        update_categoria: bool = False,
    ) -> SupplierReadSchema | None:
        with get_session() as session:
            row = session.execute(
                select(FornecedorRef, PessoaRef)
                .join(PessoaRef, PessoaRef.id_pessoa == FornecedorRef.id_pessoa)
                .where(FornecedorRef.id_fornecedor == supplier_id)
            ).first()
            if row is None:
                return None
            fornecedor, pessoa = row
            if nome is not None:
                pessoa.nome = nome
            if documento is not None:
                pessoa.documento = documento
            if update_categoria:
                fornecedor.categoria = categoria
            session.flush()
            return _supplier_read(fornecedor, pessoa)

    def delete(self, supplier_id: int) -> bool:
        with get_session() as session:
            fornecedor = session.get(FornecedorRef, supplier_id)
            if fornecedor is None:
                return False
            session.delete(fornecedor)
            return True


class PurchaseLookupRepository:
    """Read-only access to shared catalog tables for purchases UI labels."""

    def list_products(self) -> list[tuple[ProdutoRef, UnidadeMedidaRef]]:
        with get_session() as session:
            rows = session.execute(
                select(ProdutoRef, UnidadeMedidaRef)
                .select_from(ProdutoRef)
                .join(UnidadeMedidaRef, UnidadeMedidaRef.id_unidade == ProdutoRef.id_unidade)
                .order_by(ProdutoRef.nome)
            ).all()
            result: list[tuple[ProdutoRef, UnidadeMedidaRef]] = []
            for produto, unidade in rows:
                session.expunge(produto)
                # Same UnidadeMedidaRef instance is reused when products share a unit.
                if unidade in session:
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
