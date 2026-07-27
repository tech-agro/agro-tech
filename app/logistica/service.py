"""Logistics domain use cases.

Integração entre módulos (visão de negócio):

Recebe informações de:
- Estoque: lotes disponíveis para expedição com saldo disponível
  (a Produção já disponibilizou os produtos na colheita; a Logística
  consulta o Estoque, não a Produção diretamente).
- Comercial: vendas confirmadas e sugestões de cargas baseadas no picking.

Envia informações para:
- Comercial: atualização do status da expedição (EXPEDIDA e ENTREGUE).
- Estoque: registro de saídas por venda e transferências entre locais.
- Financeiro: registro dos custos logísticos da operação.
- Inteligência: atualização de indicadores logísticos
  (expedições, entregas, custos e desempenho operacional).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.core.database import get_session
from app.logistica.enum import DispatchStatus, OperationStatus, OperationType, VehicleType
from app.logistica.errors import LogisticsError
from app.logistica.models.dispatch import DispatchModel
from app.logistica.models.load import LoadModel
from app.logistica.models.operation import OperationModel
from app.logistica.repository import (
    AddressRepository,
    DispatchRepository,
    LoadRepository,
    LocationRepository,
    LogisticsLookupRepository,
    OperationRepository,
    VehicleRepository,
    WeighingRepository,
)
from app.logistica.schemas.dispatch import (
    DispatchCreateSchema,
    DispatchReadSchema,
    DispatchUpdateSchema,
)
from app.logistica.schemas.load import LoadCreateSchema, LoadReadSchema, LoadUpdateSchema
from app.logistica.schemas.lookups import (
    DriverOptionSchema,
    LocationOptionSchema,
    LotOptionSchema,
    SaleOptionSchema,
    VehicleOptionSchema,
    VehicleTypeOptionSchema,
)
from app.logistica.schemas.location import (
    LocationCreateSchema,
    LocationReadSchema,
    LocationUpdateSchema,
)
from app.logistica.schemas.address import AddressReadSchema
from app.logistica.schemas.operation import (
    OperationCreateSchema,
    OperationReadSchema,
    OperationUpdateSchema,
)
from app.logistica.schemas.vehicle import (
    VehicleCreateSchema,
    VehicleReadSchema,
    VehicleUpdateSchema,
)
from app.logistica.schemas.weighing import (
    WeighingCreateSchema,
    WeighingReadSchema,
    WeighingUpdateSchema,
)

_LOAD_EDITABLE_STATUSES = frozenset(
    {OperationStatus.ABERTA, OperationStatus.EM_ANDAMENTO}
)
_ACTIVE_OPERATION_STATUSES = frozenset(
    {OperationStatus.ABERTA, OperationStatus.EM_ANDAMENTO}
)


class LogisticsService:
    """Orchestrates fleet catalog, operations, loads, weighings, and dispatches."""

    def __init__(
        self,
        vehicle_repo: VehicleRepository | None = None,
        address_repo: AddressRepository | None = None,
        location_repo: LocationRepository | None = None,
        operation_repo: OperationRepository | None = None,
        load_repo: LoadRepository | None = None,
        weighing_repo: WeighingRepository | None = None,
        dispatch_repo: DispatchRepository | None = None,
        lookup_repo: LogisticsLookupRepository | None = None,
    ) -> None:
        self.vehicle_repo = vehicle_repo or VehicleRepository()
        self.address_repo = address_repo or AddressRepository()
        self.location_repo = location_repo or LocationRepository()
        self.operation_repo = operation_repo or OperationRepository()
        self.load_repo = load_repo or LoadRepository()
        self.weighing_repo = weighing_repo or WeighingRepository()
        self.dispatch_repo = dispatch_repo or DispatchRepository()
        self.lookup_repo = lookup_repo or LogisticsLookupRepository()

    @staticmethod
    def _assert_period(data_inicio, data_fim) -> None:
        if data_fim is not None and data_inicio is not None and data_fim < data_inicio:
            raise LogisticsError("data_fim must be on or after data_inicio")

    def _ensure_operation_load_editable(self, operation_id: int):
        operation = self.operation_repo.get_by_id(operation_id)
        if operation is None:
            return None
        if operation.status not in _LOAD_EDITABLE_STATUSES:
            raise LogisticsError(
                f"Operation in status {operation.status.value} does not allow load changes"
            )
        return operation

    def _ensure_operation_active(self, operation_id: int):
        operation = self.operation_repo.get_by_id(operation_id)
        if operation is None:
            return None
        if operation.status not in _ACTIVE_OPERATION_STATUSES:
            raise LogisticsError(
                f"Operation in status {operation.status.value} does not allow "
                "weighing or dispatch changes"
            )
        return operation

    def _get_load_for_operation(self, operation_id: int, load_id: int):
        load = self.load_repo.get_by_id(load_id)
        if load is None or load.id_operacao != operation_id:
            return None
        return load

    @staticmethod
    def _to_operation_read(
        operation: OperationModel,
        veiculo_placa: str | None,
        origem_nome: str | None,
        destino_nome: str | None,
        cliente_nome: str | None,
    ) -> OperationReadSchema:
        data = OperationReadSchema.model_validate(operation).model_dump()
        data["veiculo_placa"] = veiculo_placa
        data["origem_nome"] = origem_nome
        data["destino_nome"] = destino_nome
        data["cliente_nome"] = cliente_nome
        return OperationReadSchema.model_validate(data)

    @staticmethod
    def _to_load_read(
        load: LoadModel, lote_codigo: str | None, produto_nome: str | None
    ) -> LoadReadSchema:
        data = LoadReadSchema.model_validate(load).model_dump()
        data["lote_codigo"] = lote_codigo
        data["produto_nome"] = produto_nome
        return LoadReadSchema.model_validate(data)

    @staticmethod
    def _to_vehicle_read(vehicle) -> VehicleReadSchema:
        return VehicleReadSchema.model_validate(vehicle)

    def _load_operation_read(self, operation_id: int) -> OperationReadSchema | None:
        loaded = self.operation_repo.get_with_labels(operation_id)
        if loaded is None:
            return None
        operation, placa, origem, destino, cliente = loaded
        return self._to_operation_read(operation, placa, origem, destino, cliente)

    def _load_load_read(self, load_id: int) -> LoadReadSchema | None:
        loaded = self.load_repo.get_with_lot_labels(load_id)
        if loaded is None:
            return None
        load, codigo, produto = loaded
        return self._to_load_read(load, codigo, produto)

    @staticmethod
    def _resolve_dispatch_status(
        *,
        data_saida: datetime | None,
        data_entrega: datetime | None,
        cancelled: bool = False,
        has_load: bool = True,
    ) -> DispatchStatus:
        """Automatic expedition status from operational events."""
        if cancelled:
            return DispatchStatus.CANCELADA
        if data_entrega is not None:
            return DispatchStatus.ENTREGUE
        if data_saida is not None:
            return DispatchStatus.EXPEDIDA
        if has_load:
            return DispatchStatus.EM_PREPARACAO
        return DispatchStatus.PENDENTE

    def _ensure_dispatch_for_load(self, load_id: int) -> None:
        if self.dispatch_repo.get_by_load(load_id) is not None:
            return
        self.dispatch_repo.create(
            {
                "id_carga": load_id,
                "status": DispatchStatus.EM_PREPARACAO,
            }
        )

    def _cancel_dispatches_for_operation(self, operation_id: int) -> None:
        for load in self.load_repo.list(filters={"id_operacao": operation_id}):
            dispatch = self.dispatch_repo.get_by_load(load.id_carga)
            if dispatch is None:
                continue
            self.dispatch_repo.update(
                dispatch.id_expedicao, {"status": DispatchStatus.CANCELADA}
            )

    def _sync_operation_from_dispatches(self, operation_id: int) -> None:
        """Alinha status gerencial da operacao ao progresso das expedicoes.

        Operacao criada (sem carga) → ABERTA
        Carga / execucao / saida → EM_ANDAMENTO
        Todas entregues → CONCLUIDA
        (CANCELADA e definida explicitamente na operacao)
        """
        operation = self.operation_repo.get_by_id(operation_id)
        if operation is None or operation.status == OperationStatus.CANCELADA:
            return

        loads = self.load_repo.list(filters={"id_operacao": operation_id})
        if not loads:
            if operation.status != OperationStatus.ABERTA:
                self.operation_repo.update(
                    operation_id, {"status": OperationStatus.ABERTA}
                )
            return

        statuses: list[DispatchStatus] = []
        for load in loads:
            dispatch = self.dispatch_repo.get_by_load(load.id_carga)
            if dispatch is not None:
                statuses.append(dispatch.status)

        if (
            statuses
            and len(statuses) == len(loads)
            and all(s == DispatchStatus.ENTREGUE for s in statuses)
        ):
            if operation.status != OperationStatus.CONCLUIDA:
                self.operation_repo.update(
                    operation_id, {"status": OperationStatus.CONCLUIDA}
                )
            return

        if operation.status != OperationStatus.EM_ANDAMENTO:
            self.operation_repo.update(
                operation_id, {"status": OperationStatus.EM_ANDAMENTO}
            )

    # --- Lookups ---

    def list_vehicle_type_options(self) -> list[VehicleTypeOptionSchema]:
        return [VehicleTypeOptionSchema(tipo=item) for item in VehicleType]

    def list_vehicle_options(self) -> list[VehicleOptionSchema]:
        return [
            VehicleOptionSchema(
                id_veiculo=vehicle.id_veiculo,
                placa=vehicle.placa,
                tipo=vehicle.tipo,
                capacidade=float(vehicle.capacidade)
                if vehicle.capacidade is not None
                else None,
            )
            for vehicle in self.lookup_repo.list_vehicles()
        ]

    def list_location_options(self) -> list[LocationOptionSchema]:
        return [
            LocationOptionSchema.model_validate(row)
            for row in self.lookup_repo.list_locations()
        ]

    def list_sale_options(self) -> list[SaleOptionSchema]:
        return [
            SaleOptionSchema(
                id_venda=venda.id_venda,
                cliente_nome=nome,
                data_venda=venda.data_venda,
                valor_total=float(venda.valor_total),
            )
            for venda, nome in self.lookup_repo.list_sales()
        ]

    def list_lot_options(self) -> list[LotOptionSchema]:
        return [
            LotOptionSchema(
                id_lote=lote.id_lote,
                codigo_lote=lote.codigo_lote,
                produto_nome=nome,
            )
            for lote, nome in self.lookup_repo.list_lots()
        ]

    def list_driver_options(self) -> list[DriverOptionSchema]:
        return [
            DriverOptionSchema(
                id_funcionario=funcionario.id_funcionario,
                nome=nome,
                cargo=funcionario.cargo,
                setor=funcionario.setor,
            )
            for funcionario, nome in self.lookup_repo.list_drivers()
        ]

    # --- Vehicles ---

    def create_vehicle(self, payload: VehicleCreateSchema) -> VehicleReadSchema:
        try:
            record = self.vehicle_repo.create(payload.model_dump())
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not create vehicle. Check that placa is unique."
            ) from exc
        loaded = self.vehicle_repo.get_by_id(record.id_veiculo)
        assert loaded is not None
        return self._to_vehicle_read(loaded)

    def list_vehicles(self) -> list[VehicleReadSchema]:
        return [
            self._to_vehicle_read(vehicle)
            for vehicle in self.vehicle_repo.list()
        ]

    def get_vehicle(self, vehicle_id: int) -> VehicleReadSchema | None:
        loaded = self.vehicle_repo.get_by_id(vehicle_id)
        if loaded is None:
            return None
        return self._to_vehicle_read(loaded)

    def update_vehicle(
        self, vehicle_id: int, payload: VehicleUpdateSchema
    ) -> VehicleReadSchema | None:
        if self.vehicle_repo.get_by_id(vehicle_id) is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        try:
            record = self.vehicle_repo.update(vehicle_id, data)
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not update vehicle. Check that placa is unique."
            ) from exc
        if record is None:
            return None
        return self.get_vehicle(vehicle_id)

    def delete_vehicle(self, vehicle_id: int) -> bool:
        ops = self.operation_repo.list(filters={"id_veiculo": vehicle_id})
        if ops:
            raise LogisticsError("Cannot delete vehicle linked to operations")
        return self.vehicle_repo.delete(vehicle_id)

    # --- Locations ---

    @staticmethod
    def _to_location_read(location, address) -> LocationReadSchema:
        data = LocationReadSchema.model_validate(location).model_dump()
        data["endereco"] = (
            AddressReadSchema.model_validate(address) if address is not None else None
        )
        return LocationReadSchema.model_validate(data)

    def create_location(self, payload: LocationCreateSchema) -> LocationReadSchema:
        id_endereco = payload.id_endereco
        if payload.endereco is not None:
            address = self.address_repo.create(payload.endereco.model_dump())
            id_endereco = address.id_endereco
        elif id_endereco is not None and self.address_repo.get_by_id(id_endereco) is None:
            raise LogisticsError("Address not found")
        try:
            record = self.location_repo.create(
                {
                    "nome": payload.nome.strip(),
                    "tipo": payload.tipo,
                    "id_endereco": id_endereco,
                }
            )
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not create location. Check that nome+tipo is unique."
            ) from exc
        loaded = self.location_repo.get_with_address(record.id_local_logistico)
        assert loaded is not None
        return self._to_location_read(*loaded)

    def list_locations(self) -> list[LocationReadSchema]:
        return [
            self._to_location_read(location, address)
            for location, address in self.location_repo.list_with_address()
        ]

    def get_location(self, location_id: int) -> LocationReadSchema | None:
        loaded = self.location_repo.get_with_address(location_id)
        if loaded is None:
            return None
        return self._to_location_read(*loaded)

    def update_location(
        self, location_id: int, payload: LocationUpdateSchema
    ) -> LocationReadSchema | None:
        current = self.location_repo.get_by_id(location_id)
        if current is None:
            return None
        data = payload.model_dump(exclude_unset=True, exclude={"endereco"})
        if payload.endereco is not None:
            address = self.address_repo.create(payload.endereco.model_dump())
            data["id_endereco"] = address.id_endereco
        elif "id_endereco" in data and data["id_endereco"] is not None:
            if self.address_repo.get_by_id(data["id_endereco"]) is None:
                raise LogisticsError("Address not found")
        if "nome" in data and isinstance(data["nome"], str):
            data["nome"] = data["nome"].strip()
        try:
            self.location_repo.update(location_id, data)
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not update location. Check that nome+tipo is unique."
            ) from exc
        return self.get_location(location_id)

    def delete_location(self, location_id: int) -> bool:
        as_origin = self.operation_repo.list(filters={"id_origem": location_id})
        as_destination = self.operation_repo.list(filters={"id_destino": location_id})
        if as_origin or as_destination:
            raise LogisticsError("Cannot delete location linked to operations")
        return self.location_repo.delete(location_id)

    # --- Operations ---

    def _assert_operation_endpoints(self, id_origem: int, id_destino: int) -> None:
        if id_origem == id_destino:
            raise LogisticsError("origem and destino must be different")
        if self.location_repo.get_by_id(id_origem) is None:
            raise LogisticsError("Origin location not found")
        if self.location_repo.get_by_id(id_destino) is None:
            raise LogisticsError("Destination location not found")

    def create_operation(self, payload: OperationCreateSchema) -> OperationReadSchema:
        self._assert_period(payload.data_inicio, payload.data_fim)
        self._assert_operation_endpoints(payload.id_origem, payload.id_destino)
        cargas = list(payload.cargas)
        if payload.suggest_loads_from_sale and payload.id_venda is not None and not cargas:
            cargas = self._suggest_loads_from_sale(payload.id_venda)
        header = payload.model_dump(exclude={"cargas", "suggest_loads_from_sale"})
        try:
            with get_session() as session:
                operation = OperationModel(**header)
                session.add(operation)
                session.flush()
                operation_id = operation.id_operacao
                for load in cargas:
                    load_row = LoadModel(id_operacao=operation_id, **load.model_dump())
                    session.add(load_row)
                    session.flush()
                    session.add(
                        DispatchModel(
                            id_carga=load_row.id_carga,
                            status=DispatchStatus.EM_PREPARACAO,
                        )
                    )
                session.flush()
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not create operation. Check that id_veiculo, id_origem, "
                "id_destino, id_venda and id_lote exist."
            ) from exc
        if cargas:
            self.operation_repo.update(
                operation_id, {"status": OperationStatus.EM_ANDAMENTO}
            )
        loaded = self._load_operation_read(operation_id)
        assert loaded is not None
        return loaded

    def _suggest_loads_from_sale(self, sale_id: int) -> list[LoadCreateSchema]:
        """Comercial: sugestão de cargas baseada no picking da venda."""
        try:
            from app.comercial.service import CommercialService

            suggestions = CommercialService().list_picking_suggestion(sale_id)
        except Exception as exc:
            raise LogisticsError(
                "Could not suggest loads from sale. Confirm the sale first."
            ) from exc
        return [
            LoadCreateSchema(
                id_lote=s["id_lote"],
                id_item_venda=s["id_item_venda"],
                quantidade=s["quantidade"],
            )
            for s in suggestions
        ]
    def list_operations(self) -> list[OperationReadSchema]:
        return [
            self._to_operation_read(operation, placa, origem, destino, cliente)
            for operation, placa, origem, destino, cliente in self.operation_repo.list_with_labels()
        ]

    def get_operation(self, operation_id: int) -> OperationReadSchema | None:
        return self._load_operation_read(operation_id)

    def update_operation(
        self, operation_id: int, payload: OperationUpdateSchema
    ) -> OperationReadSchema | None:
        previous = self.operation_repo.get_by_id(operation_id)
        if previous is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        data_inicio = data.get("data_inicio", previous.data_inicio)
        data_fim = data.get("data_fim", previous.data_fim)
        self._assert_period(data_inicio, data_fim)

        id_origem = data.get("id_origem", previous.id_origem)
        id_destino = data.get("id_destino", previous.id_destino)
        self._assert_operation_endpoints(id_origem, id_destino)

        try:
            record = self.operation_repo.update(operation_id, data)
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not update operation. Check that id_veiculo, id_origem, "
                "id_destino and id_venda exist."
            ) from exc
        if record is None:
            return None
        if data.get("status") == OperationStatus.CANCELADA:
            self._cancel_dispatches_for_operation(operation_id)
        return self._load_operation_read(operation_id)

    def delete_operation(self, operation_id: int) -> bool:
        if self.operation_repo.get_by_id(operation_id) is None:
            return False
        for load in self.load_repo.list(filters={"id_operacao": operation_id}):
            self._delete_load_children(load.id_carga)
            self.load_repo.delete(load.id_carga)
        return self.operation_repo.delete(operation_id)

    def _delete_load_children(self, load_id: int) -> None:
        for weighing in self.weighing_repo.list(filters={"id_carga": load_id}):
            self.weighing_repo.delete(weighing.id_pesagem)
        dispatch = self.dispatch_repo.get_by_load(load_id)
        if dispatch is not None:
            self.dispatch_repo.delete(dispatch.id_expedicao)

    # --- Loads (nested under operation) ---

    def add_load(
        self, operation_id: int, payload: LoadCreateSchema
    ) -> LoadReadSchema | None:
        if self._ensure_operation_load_editable(operation_id) is None:
            return None
        data = payload.model_dump()
        data["id_operacao"] = operation_id
        try:
            record = self.load_repo.create(data)
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not add load. Check that id_lote exists."
            ) from exc
        # Evento: carga adicionada → expedicao EM_PREPARACAO; operacao EM_ANDAMENTO
        self._ensure_dispatch_for_load(record.id_carga)
        self._sync_operation_from_dispatches(operation_id)
        return self._load_load_read(record.id_carga)

    def list_loads(self, operation_id: int) -> list[LoadReadSchema] | None:
        if self.operation_repo.get_by_id(operation_id) is None:
            return None
        return [
            self._to_load_read(load, codigo, produto)
            for load, codigo, produto in self.load_repo.list_with_lot_labels(
                operation_id
            )
        ]

    def list_all_loads(self) -> list[LoadReadSchema]:
        return [
            self._to_load_read(load, codigo, produto)
            for load, codigo, produto in self.load_repo.list_all_with_lot_labels()
        ]

    def get_load(self, load_id: int) -> LoadReadSchema | None:
        return self._load_load_read(load_id)

    def update_load(
        self, operation_id: int, load_id: int, payload: LoadUpdateSchema
    ) -> LoadReadSchema | None:
        if self._ensure_operation_load_editable(operation_id) is None:
            return None
        if self._get_load_for_operation(operation_id, load_id) is None:
            return None
        try:
            record = self.load_repo.update(
                load_id, payload.model_dump(exclude_unset=True)
            )
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not update load. Check that id_lote exists."
            ) from exc
        if record is None:
            return None
        return self._load_load_read(load_id)

    def delete_load(self, operation_id: int, load_id: int) -> bool:
        if self._ensure_operation_load_editable(operation_id) is None:
            return False
        if self._get_load_for_operation(operation_id, load_id) is None:
            return False
        self._delete_load_children(load_id)
        ok = self.load_repo.delete(load_id)
        if ok:
            self._sync_operation_from_dispatches(operation_id)
        return ok

    # --- Weighings (nested under operation/load) ---

    def add_weighing(
        self, operation_id: int, load_id: int, payload: WeighingCreateSchema
    ) -> WeighingReadSchema | None:
        if self._ensure_operation_active(operation_id) is None:
            return None
        if self._get_load_for_operation(operation_id, load_id) is None:
            return None
        data = payload.model_dump()
        data["id_carga"] = load_id
        try:
            record = self.weighing_repo.create(data)
        except IntegrityError as exc:
            raise LogisticsError("Could not add weighing") from exc
        return WeighingReadSchema.model_validate(record)

    def list_weighings(
        self, operation_id: int, load_id: int
    ) -> list[WeighingReadSchema] | None:
        if self.operation_repo.get_by_id(operation_id) is None:
            return None
        if self._get_load_for_operation(operation_id, load_id) is None:
            return None
        return [
            WeighingReadSchema.model_validate(r)
            for r in self.weighing_repo.list(filters={"id_carga": load_id})
        ]

    def update_weighing(
        self,
        operation_id: int,
        load_id: int,
        weighing_id: int,
        payload: WeighingUpdateSchema,
    ) -> WeighingReadSchema | None:
        if self._ensure_operation_active(operation_id) is None:
            return None
        if self._get_load_for_operation(operation_id, load_id) is None:
            return None
        weighing = self.weighing_repo.get_by_id(weighing_id)
        if weighing is None or weighing.id_carga != load_id:
            return None
        record = self.weighing_repo.update(
            weighing_id, payload.model_dump(exclude_unset=True)
        )
        if record is None:
            return None
        return WeighingReadSchema.model_validate(record)

    def delete_weighing(
        self, operation_id: int, load_id: int, weighing_id: int
    ) -> bool:
        if self._ensure_operation_active(operation_id) is None:
            return False
        if self._get_load_for_operation(operation_id, load_id) is None:
            return False
        weighing = self.weighing_repo.get_by_id(weighing_id)
        if weighing is None or weighing.id_carga != load_id:
            return False
        return self.weighing_repo.delete(weighing_id)

    def _to_dispatch_read(
        self, dispatch, motorista_nome: str | None
    ) -> DispatchReadSchema:
        data = DispatchReadSchema.model_validate(dispatch).model_dump()
        data["motorista_nome"] = motorista_nome
        return DispatchReadSchema.model_validate(data)

    def _load_dispatch_read(self, load_id: int) -> DispatchReadSchema | None:
        loaded = self.dispatch_repo.get_with_driver_name(load_id)
        if loaded is None:
            return None
        dispatch, nome = loaded
        return self._to_dispatch_read(dispatch, nome)

    def _assert_driver(self, id_funcionario: int | None) -> None:
        if id_funcionario is None:
            return
        drivers = {
            f.id_funcionario for f, _ in self.lookup_repo.list_drivers()
        }
        if id_funcionario not in drivers:
            raise LogisticsError("Driver not found")

    # --- Dispatch (1:1 with load) ---

    def create_dispatch(
        self, operation_id: int, load_id: int, payload: DispatchCreateSchema
    ) -> DispatchReadSchema | None:
        if self._ensure_operation_active(operation_id) is None:
            return None
        if self._get_load_for_operation(operation_id, load_id) is None:
            return None
        if self.dispatch_repo.get_by_load(load_id) is not None:
            raise LogisticsError("Load already has a dispatch (1:1)")
        data = payload.model_dump(exclude_unset=True)
        self._assert_driver(data.get("id_funcionario"))
        data["id_carga"] = load_id
        data["status"] = self._resolve_dispatch_status(
            data_saida=data.get("data_saida"),
            data_entrega=data.get("data_entrega"),
            has_load=True,
        )
        try:
            record = self.dispatch_repo.create(data)
        except IntegrityError as exc:
            raise LogisticsError(
                "Could not create dispatch. Load may already have one."
            ) from exc
        self._sync_operation_from_dispatches(operation_id)
        return self._load_dispatch_read(load_id)

    def get_dispatch(
        self, operation_id: int, load_id: int
    ) -> DispatchReadSchema | None:
        if self.operation_repo.get_by_id(operation_id) is None:
            return None
        if self._get_load_for_operation(operation_id, load_id) is None:
            return None
        return self._load_dispatch_read(load_id)

    def update_dispatch(
        self, operation_id: int, load_id: int, payload: DispatchUpdateSchema
    ) -> DispatchReadSchema | None:
        if self._ensure_operation_active(operation_id) is None:
            return None
        if self._get_load_for_operation(operation_id, load_id) is None:
            return None
        record = self.dispatch_repo.get_by_load(load_id)
        if record is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        if "id_funcionario" in data:
            self._assert_driver(data.get("id_funcionario"))
        data_saida = data["data_saida"] if "data_saida" in data else record.data_saida
        data_entrega = (
            data["data_entrega"] if "data_entrega" in data else record.data_entrega
        )
        cancelled = record.status == DispatchStatus.CANCELADA or data.get(
            "status"
        ) == DispatchStatus.CANCELADA
        data["status"] = self._resolve_dispatch_status(
            data_saida=data_saida,
            data_entrega=data_entrega,
            cancelled=cancelled,
            has_load=True,
        )
        updated = self.dispatch_repo.update(record.id_expedicao, data)
        if updated is None:
            return None

        previous_status = record.status
        new_status = updated.status
        transitioned_to_shipped = (
            new_status in {DispatchStatus.EXPEDIDA, DispatchStatus.ENTREGUE}
            and previous_status
            not in {DispatchStatus.EXPEDIDA, DispatchStatus.ENTREGUE}
        )
        transitioned_to_delivered = (
            new_status == DispatchStatus.ENTREGUE
            and previous_status != DispatchStatus.ENTREGUE
        )

        if transitioned_to_shipped:
            self._propagate_stock_on_ship(operation_id, load_id)
            self._notify_commercial(
                operation_id, shipped=True, delivered=new_status == DispatchStatus.ENTREGUE
            )
            self._notify_financial(operation_id)
            self._notify_intelligence(
                operation_id,
                evento="expedicao_iniciada",
                indicador_nome="Expedicoes iniciadas",
            )

        if transitioned_to_delivered:
            self._notify_commercial(operation_id, shipped=True, delivered=True)
            self._notify_intelligence(
                operation_id,
                evento="entrega_confirmada",
                indicador_nome="Entregas logisticas concluidas",
            )

        self._sync_operation_from_dispatches(operation_id)
        return self._load_dispatch_read(load_id)

    def _resolve_stock_accounts(
        self, operation_id: int, load_id: int
    ) -> tuple[int | None, int | None, int | None, float | None]:
        """Return (id_estoque_origem, id_estoque_destino, id_produto, quantidade)."""
        from sqlalchemy import text

        operation = self.operation_repo.get_by_id(operation_id)
        load = self.load_repo.get_by_id(load_id)
        if operation is None or load is None:
            return None, None, None, None

        with get_session() as session:
            from app.logistica.models.refs import LoteRef

            lote = session.get(LoteRef, load.id_lote)
            if lote is None:
                return None, None, None, None
            id_produto = lote.id_produto

            origem = session.execute(
                text(
                    """
                    SELECT id_local_armazenamento
                    FROM local_logistico
                    WHERE id_local_logistico = :id
                    """
                ),
                {"id": operation.id_origem},
            ).first()
            destino = session.execute(
                text(
                    """
                    SELECT id_local_armazenamento
                    FROM local_logistico
                    WHERE id_local_logistico = :id
                    """
                ),
                {"id": operation.id_destino},
            ).first()

            id_estoque_origem = None
            id_estoque_destino = None
            if origem and origem[0] is not None:
                row = session.execute(
                    text(
                        "SELECT id_estoque FROM estoque WHERE id_local = :id LIMIT 1"
                    ),
                    {"id": int(origem[0])},
                ).first()
                if row:
                    id_estoque_origem = int(row[0])
            if destino and destino[0] is not None:
                row = session.execute(
                    text(
                        "SELECT id_estoque FROM estoque WHERE id_local = :id LIMIT 1"
                    ),
                    {"id": int(destino[0])},
                ).first()
                if row:
                    id_estoque_destino = int(row[0])

            if id_estoque_origem is None and load.id_item_venda is not None:
                row = session.execute(
                    text(
                        """
                        SELECT id_estoque FROM item_venda_lote
                        WHERE id_item_venda = :item AND id_lote = :lote
                        LIMIT 1
                        """
                    ),
                    {"item": load.id_item_venda, "lote": load.id_lote},
                ).first()
                if row:
                    id_estoque_origem = int(row[0])

            if id_estoque_origem is None:
                row = session.execute(
                    text(
                        """
                        SELECT id_estoque FROM saldo_lote
                        WHERE id_lote = :lote
                        ORDER BY quantidade_atual DESC
                        LIMIT 1
                        """
                    ),
                    {"lote": load.id_lote},
                ).first()
                if row:
                    id_estoque_origem = int(row[0])

        return (
            id_estoque_origem,
            id_estoque_destino,
            id_produto,
            float(load.quantidade) if load.quantidade is not None else None,
        )

    def _propagate_stock_on_ship(self, operation_id: int, load_id: int) -> None:
        """Estoque: registra saída por venda ou transferência entre locais."""
        from decimal import Decimal

        from app.estoque.service import EstoqueService

        operation = self.operation_repo.get_by_id(operation_id)
        load = self.load_repo.get_by_id(load_id)
        if operation is None or load is None or load.quantidade is None:
            return

        id_origem, id_destino, id_produto, qty = self._resolve_stock_accounts(
            operation_id, load_id
        )
        if id_produto is None or qty is None:
            return

        inventory = EstoqueService()
        if operation.tipo == OperationType.TRANSFERENCIA:
            if id_origem is None or id_destino is None:
                return
            inventory.register_transfer(
                id_estoque_origem=id_origem,
                id_estoque_destino=id_destino,
                id_produto=id_produto,
                id_lote=load.id_lote,
                quantidade=Decimal(str(qty)),
            )
            return

        if id_origem is None:
            return
        inventory.register_exit_from_dispatch(
            id_estoque=id_origem,
            id_produto=id_produto,
            id_lote=load.id_lote,
            quantidade=Decimal(str(qty)),
            id_item_venda=load.id_item_venda,
        )

    def _notify_commercial(
        self, operation_id: int, *, shipped: bool, delivered: bool
    ) -> None:
        """Comercial: atualiza o status da expedição (EXPEDIDA / ENTREGUE)."""
        operation = self.operation_repo.get_by_id(operation_id)
        if operation is None or operation.id_venda is None:
            return
        try:
            from app.comercial.service import CommercialService

            CommercialService().register_shipment_status(
                operation.id_venda, shipped=shipped, delivered=delivered
            )
        except Exception:
            return

    def _notify_financial(self, operation_id: int) -> None:
        """Financeiro: registra os custos logísticos da operação."""
        operation = self.operation_repo.get_by_id(operation_id)
        if operation is None or operation.custo_previsto is None:
            return
        try:
            from app.financeiro.service import FinanceiroService

            FinanceiroService().register_logistics_cost(
                id_operacao=operation_id,
                valor=operation.custo_previsto,
            )
            from app.inteligencia.service import InteligenciaService

            InteligenciaService().register_logistics_kpi(
                indicador_nome="Custo logistico acumulado",
                valor=operation.custo_previsto,
                unidade="BRL",
            )
        except Exception:
            return

    def receber_venda_confirmada(self, id_venda: int) -> None:
        """Chamado pela Comercial quando uma venda e confirmada.

        Implementacao futura:
            - abrir uma `operacao_logistica` (ordem de carregamento) vinculada
              a venda, com veiculo e rota a definir.

        Mantido como placeholder ate a implementacao do modulo Logistica.
        """
        return None

    def _notify_intelligence(
        self, operation_id: int, *, evento: str, indicador_nome: str
    ) -> None:
        """Inteligência: atualiza indicadores logísticos operacionais."""
        try:
            from app.inteligencia.service import InteligenciaService

            InteligenciaService().register_logistics_kpi(
                indicador_nome=indicador_nome,
                valor=1,
                unidade="UN",
            )
        except Exception:
            return

    def _request_stock_exit_for_load(self, load_id: int) -> None:
        """Legacy helper kept for compatibility; prefer _propagate_stock_on_ship."""
        load = self.load_repo.get_by_id(load_id)
        if load is None:
            return
        operation_id = load.id_operacao
        self._propagate_stock_on_ship(operation_id, load_id)

    def delete_dispatch(self, operation_id: int, load_id: int) -> bool:
        if self._ensure_operation_active(operation_id) is None:
            return False
        if self._get_load_for_operation(operation_id, load_id) is None:
            return False
        record = self.dispatch_repo.get_by_load(load_id)
        if record is None:
            return False
        if record.status in {DispatchStatus.EXPEDIDA, DispatchStatus.ENTREGUE}:
            raise LogisticsError(
                "Cannot delete dispatch after it has been shipped or delivered"
            )
        return self.dispatch_repo.delete(record.id_expedicao)
