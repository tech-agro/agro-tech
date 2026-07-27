"""Data access for the logistics domain."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.core.base_repository import BaseRepository
from app.core.database import get_session
from app.logistica.models.address import AddressModel
from app.logistica.models.dispatch import DispatchModel
from app.logistica.models.load import LoadModel
from app.logistica.models.location import LogisticsLocationModel
from app.logistica.models.operation import OperationModel
from app.logistica.models.refs import (
    ClienteRef,
    FuncionarioRef,
    LoteRef,
    PessoaRef,
    ProdutoRef,
    VendaRef,
)
from app.logistica.models.vehicle import VehicleModel
from app.logistica.models.weighing import WeighingModel

# Register FK targets on SQLAlchemy metadata (shared tables owned elsewhere).
_ = (PessoaRef, ClienteRef, VendaRef, ProdutoRef, LoteRef, FuncionarioRef)


class VehicleRepository(BaseRepository[VehicleModel]):
    model = VehicleModel


class AddressRepository(BaseRepository[AddressModel]):
    model = AddressModel


class LocationRepository(BaseRepository[LogisticsLocationModel]):
    model = LogisticsLocationModel

    def list_with_address(
        self,
    ) -> list[tuple[LogisticsLocationModel, AddressModel | None]]:
        with get_session() as session:
            rows = session.execute(
                select(LogisticsLocationModel, AddressModel)
                .outerjoin(
                    AddressModel,
                    AddressModel.id_endereco == LogisticsLocationModel.id_endereco,
                )
                .order_by(LogisticsLocationModel.nome)
            ).all()
            result: list[tuple[LogisticsLocationModel, AddressModel | None]] = []
            for location, address in rows:
                session.expunge(location)
                if address is not None:
                    session.expunge(address)
                result.append((location, address))
            return result

    def get_with_address(
        self, location_id: int
    ) -> tuple[LogisticsLocationModel, AddressModel | None] | None:
        with get_session() as session:
            row = session.execute(
                select(LogisticsLocationModel, AddressModel)
                .outerjoin(
                    AddressModel,
                    AddressModel.id_endereco == LogisticsLocationModel.id_endereco,
                )
                .where(LogisticsLocationModel.id_local_logistico == location_id)
            ).first()
            if row is None:
                return None
            location, address = row
            session.expunge(location)
            if address is not None:
                session.expunge(address)
            return location, address


class OperationRepository(BaseRepository[OperationModel]):
    model = OperationModel

    def list_with_labels(
        self,
    ) -> list[
        tuple[OperationModel, str | None, str | None, str | None, str | None]
    ]:
        origin = aliased(LogisticsLocationModel)
        destination = aliased(LogisticsLocationModel)
        with get_session() as session:
            rows = session.execute(
                select(
                    OperationModel,
                    VehicleModel.placa,
                    origin.nome,
                    destination.nome,
                    PessoaRef.nome,
                )
                .outerjoin(
                    VehicleModel, VehicleModel.id_veiculo == OperationModel.id_veiculo
                )
                .outerjoin(origin, origin.id_local_logistico == OperationModel.id_origem)
                .outerjoin(
                    destination,
                    destination.id_local_logistico == OperationModel.id_destino,
                )
                .outerjoin(VendaRef, VendaRef.id_venda == OperationModel.id_venda)
                .outerjoin(ClienteRef, ClienteRef.id_cliente == VendaRef.id_cliente)
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == ClienteRef.id_pessoa)
                .order_by(OperationModel.id_operacao)
            ).all()
            result: list[
                tuple[OperationModel, str | None, str | None, str | None, str | None]
            ] = []
            for operation, placa, origem, destino, cliente_nome in rows:
                session.expunge(operation)
                result.append((operation, placa, origem, destino, cliente_nome))
            return result

    def get_with_labels(
        self, operation_id: int
    ) -> (
        tuple[OperationModel, str | None, str | None, str | None, str | None] | None
    ):
        origin = aliased(LogisticsLocationModel)
        destination = aliased(LogisticsLocationModel)
        with get_session() as session:
            row = session.execute(
                select(
                    OperationModel,
                    VehicleModel.placa,
                    origin.nome,
                    destination.nome,
                    PessoaRef.nome,
                )
                .outerjoin(
                    VehicleModel, VehicleModel.id_veiculo == OperationModel.id_veiculo
                )
                .outerjoin(origin, origin.id_local_logistico == OperationModel.id_origem)
                .outerjoin(
                    destination,
                    destination.id_local_logistico == OperationModel.id_destino,
                )
                .outerjoin(VendaRef, VendaRef.id_venda == OperationModel.id_venda)
                .outerjoin(ClienteRef, ClienteRef.id_cliente == VendaRef.id_cliente)
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == ClienteRef.id_pessoa)
                .where(OperationModel.id_operacao == operation_id)
            ).first()
            if row is None:
                return None
            operation, placa, origem, destino, cliente_nome = row
            session.expunge(operation)
            return operation, placa, origem, destino, cliente_nome


class LoadRepository(BaseRepository[LoadModel]):
    model = LoadModel

    def list_with_lot_labels(
        self, operation_id: int
    ) -> list[tuple[LoadModel, str | None, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(LoadModel, LoteRef.codigo_lote, ProdutoRef.nome)
                .select_from(LoadModel)
                .outerjoin(LoteRef, LoteRef.id_lote == LoadModel.id_lote)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteRef.id_produto)
                .where(LoadModel.id_operacao == operation_id)
                .order_by(LoadModel.id_carga)
            ).all()
            result: list[tuple[LoadModel, str | None, str | None]] = []
            for load, codigo, produto_nome in rows:
                session.expunge(load)
                result.append((load, codigo, produto_nome))
            return result

    def list_all_with_lot_labels(
        self,
    ) -> list[tuple[LoadModel, str | None, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(LoadModel, LoteRef.codigo_lote, ProdutoRef.nome)
                .select_from(LoadModel)
                .outerjoin(LoteRef, LoteRef.id_lote == LoadModel.id_lote)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteRef.id_produto)
                .order_by(LoadModel.id_carga)
            ).all()
            result: list[tuple[LoadModel, str | None, str | None]] = []
            for load, codigo, produto_nome in rows:
                session.expunge(load)
                result.append((load, codigo, produto_nome))
            return result

    def get_with_lot_labels(
        self, load_id: int
    ) -> tuple[LoadModel, str | None, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(LoadModel, LoteRef.codigo_lote, ProdutoRef.nome)
                .select_from(LoadModel)
                .outerjoin(LoteRef, LoteRef.id_lote == LoadModel.id_lote)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteRef.id_produto)
                .where(LoadModel.id_carga == load_id)
            ).first()
            if row is None:
                return None
            load, codigo, produto_nome = row
            session.expunge(load)
            return load, codigo, produto_nome


class WeighingRepository(BaseRepository[WeighingModel]):
    model = WeighingModel


class DispatchRepository(BaseRepository[DispatchModel]):
    model = DispatchModel

    def get_by_load(self, load_id: int) -> DispatchModel | None:
        rows = self.list(filters={"id_carga": load_id})
        return rows[0] if rows else None

    def get_with_driver_name(
        self, load_id: int
    ) -> tuple[DispatchModel, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(DispatchModel, PessoaRef.nome)
                .select_from(DispatchModel)
                .outerjoin(
                    FuncionarioRef,
                    FuncionarioRef.id_funcionario == DispatchModel.id_funcionario,
                )
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == FuncionarioRef.id_pessoa)
                .where(DispatchModel.id_carga == load_id)
            ).first()
            if row is None:
                return None
            dispatch, nome = row
            session.expunge(dispatch)
            return dispatch, nome

    def get_by_id_with_driver_name(
        self, dispatch_id: int
    ) -> tuple[DispatchModel, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(DispatchModel, PessoaRef.nome)
                .select_from(DispatchModel)
                .outerjoin(
                    FuncionarioRef,
                    FuncionarioRef.id_funcionario == DispatchModel.id_funcionario,
                )
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == FuncionarioRef.id_pessoa)
                .where(DispatchModel.id_expedicao == dispatch_id)
            ).first()
            if row is None:
                return None
            dispatch, nome = row
            session.expunge(dispatch)
            return dispatch, nome


class LogisticsLookupRepository:
    """Read-only access to shared / catalog tables for logistics UI labels."""

    def list_vehicles(self) -> list[VehicleModel]:
        with get_session() as session:
            rows = session.scalars(
                select(VehicleModel).order_by(VehicleModel.placa)
            ).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def list_locations(self) -> list[LogisticsLocationModel]:
        with get_session() as session:
            rows = session.scalars(
                select(LogisticsLocationModel).order_by(LogisticsLocationModel.nome)
            ).all()
            for row in rows:
                session.expunge(row)
            return list(rows)

    def list_sales(self) -> list[tuple[VendaRef, str | None]]:
        """Confirmed sales still open for shipping/delivery (from Comercial)."""
        from sqlalchemy import String, cast

        with get_session() as session:
            rows = session.execute(
                select(VendaRef, PessoaRef.nome)
                .select_from(VendaRef)
                .outerjoin(ClienteRef, ClienteRef.id_cliente == VendaRef.id_cliente)
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == ClienteRef.id_pessoa)
                .where(
                    cast(VendaRef.status, String).in_(
                        ["CONFIRMADA", "EXPEDIDA"]
                    )
                    | (VendaRef.status.is_(None))
                )
                .order_by(VendaRef.id_venda)
            ).all()
            result: list[tuple[VendaRef, str | None]] = []
            for venda, nome in rows:
                session.expunge(venda)
                result.append((venda, nome))
            return result

    def list_lots(self) -> list[tuple[LoteRef, str | None]]:
        """Estoque: lotes disponíveis para expedição com saldo disponível.

        A Produção já disponibilizou o produto na colheita; a Logística
        consulta apenas o Estoque para saber o que pode ser carregado.
        """
        from types import SimpleNamespace

        from sqlalchemy import text

        with get_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT DISTINCT l.id_lote, l.codigo_lote, l.id_produto, p.nome
                    FROM lote l
                    JOIN saldo_lote sl ON sl.id_lote = l.id_lote
                    LEFT JOIN produto p ON p.id_produto = l.id_produto
                    WHERE (sl.quantidade_atual - sl.quantidade_reservada) > 0
                    ORDER BY l.codigo_lote
                    """
                )
            ).all()
            result: list[tuple[LoteRef, str | None]] = []
            for id_lote, codigo, id_produto, nome in rows:
                lote = SimpleNamespace(
                    id_lote=int(id_lote),
                    codigo_lote=str(codigo),
                    id_produto=int(id_produto),
                )
                result.append((lote, nome))  # type: ignore[arg-type]
            return result

    def list_drivers(self) -> list[tuple[FuncionarioRef, str]]:
        """Drivers = funcionarios with cargo Motorista (nome padrao: Motorista N)."""
        with get_session() as session:
            rows = session.execute(
                select(FuncionarioRef, PessoaRef.nome)
                .join(PessoaRef, PessoaRef.id_pessoa == FuncionarioRef.id_pessoa)
                .where(FuncionarioRef.cargo == "Motorista")
                .order_by(PessoaRef.nome)
            ).all()
            result: list[tuple[FuncionarioRef, str]] = []
            for funcionario, nome in rows:
                session.expunge(funcionario)
                result.append((funcionario, nome))
            return result
