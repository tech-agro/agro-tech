"""HTTP adapter for the logistics domain."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.logistica.errors import LogisticsError
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
from app.logistica.schemas.address import AddressLookupSchema
from app.logistica.schemas.location import (
    LocationCreateSchema,
    LocationReadSchema,
    LocationUpdateSchema,
)
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
from app.logistica.service import LogisticsService


class LogisticsController:
    """Exposes operations as main resource; loads/weighings/dispatch nest under them."""

    def __init__(self, service: LogisticsService | None = None) -> None:
        self.service = service or LogisticsService()
        self.router = APIRouter(prefix="/logistics", tags=["logistics"])
        self._register_routes()

    @staticmethod
    def _map_error(exc: LogisticsError) -> HTTPException:
        return HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    def _register_routes(self) -> None:
        self.router.get(
            "/lookups/vehicle-types", response_model=list[VehicleTypeOptionSchema]
        )(self.list_vehicle_type_options)
        self.router.get(
            "/lookups/vehicles", response_model=list[VehicleOptionSchema]
        )(self.list_vehicle_options)
        self.router.get(
            "/lookups/locations", response_model=list[LocationOptionSchema]
        )(self.list_location_options)
        self.router.get("/lookups/sales", response_model=list[SaleOptionSchema])(
            self.list_sale_options
        )
        self.router.get("/lookups/lots", response_model=list[LotOptionSchema])(
            self.list_lot_options
        )
        self.router.get("/lookups/drivers", response_model=list[DriverOptionSchema])(
            self.list_driver_options
        )
        self.router.get(
            "/addresses/by-cep/{cep}",
            response_model=AddressLookupSchema,
        )(self.lookup_address_by_cep)

        self.router.post("/vehicles", response_model=VehicleReadSchema)(
            self.create_vehicle
        )
        self.router.get("/vehicles", response_model=list[VehicleReadSchema])(
            self.list_vehicles
        )
        self.router.get("/vehicles/{vehicle_id}", response_model=VehicleReadSchema)(
            self.get_vehicle
        )
        self.router.patch("/vehicles/{vehicle_id}", response_model=VehicleReadSchema)(
            self.update_vehicle
        )
        self.router.delete(
            "/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_vehicle)

        self.router.post("/locations", response_model=LocationReadSchema)(
            self.create_location
        )
        self.router.get("/locations", response_model=list[LocationReadSchema])(
            self.list_locations
        )
        self.router.get(
            "/locations/{location_id}", response_model=LocationReadSchema
        )(self.get_location)
        self.router.patch(
            "/locations/{location_id}", response_model=LocationReadSchema
        )(self.update_location)
        self.router.delete(
            "/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_location)

        self.router.post("/operations", response_model=OperationReadSchema)(
            self.create_operation
        )
        self.router.get("/operations", response_model=list[OperationReadSchema])(
            self.list_operations
        )
        self.router.get(
            "/operations/{operation_id}", response_model=OperationReadSchema
        )(self.get_operation)
        self.router.patch(
            "/operations/{operation_id}", response_model=OperationReadSchema
        )(self.update_operation)
        self.router.delete(
            "/operations/{operation_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_operation)

        self.router.get("/loads", response_model=list[LoadReadSchema])(
            self.list_all_loads
        )
        self.router.get("/loads/{load_id}", response_model=LoadReadSchema)(
            self.get_load
        )

        self.router.post(
            "/operations/{operation_id}/loads", response_model=LoadReadSchema
        )(self.add_load)
        self.router.get(
            "/operations/{operation_id}/loads", response_model=list[LoadReadSchema]
        )(self.list_loads)
        self.router.patch(
            "/operations/{operation_id}/loads/{load_id}",
            response_model=LoadReadSchema,
        )(self.update_load)
        self.router.delete(
            "/operations/{operation_id}/loads/{load_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_load)

        self.router.post(
            "/operations/{operation_id}/loads/{load_id}/weighings",
            response_model=WeighingReadSchema,
        )(self.add_weighing)
        self.router.get(
            "/operations/{operation_id}/loads/{load_id}/weighings",
            response_model=list[WeighingReadSchema],
        )(self.list_weighings)
        self.router.patch(
            "/operations/{operation_id}/loads/{load_id}/weighings/{weighing_id}",
            response_model=WeighingReadSchema,
        )(self.update_weighing)
        self.router.delete(
            "/operations/{operation_id}/loads/{load_id}/weighings/{weighing_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_weighing)

        self.router.post(
            "/operations/{operation_id}/loads/{load_id}/dispatch",
            response_model=DispatchReadSchema,
        )(self.create_dispatch)
        self.router.get(
            "/operations/{operation_id}/loads/{load_id}/dispatch",
            response_model=DispatchReadSchema,
        )(self.get_dispatch)
        self.router.patch(
            "/operations/{operation_id}/loads/{load_id}/dispatch",
            response_model=DispatchReadSchema,
        )(self.update_dispatch)
        self.router.delete(
            "/operations/{operation_id}/loads/{load_id}/dispatch",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_dispatch)

    # --- Lookups ---

    def list_vehicle_type_options(self) -> list[VehicleTypeOptionSchema]:
        return self.service.list_vehicle_type_options()

    def list_vehicle_options(self) -> list[VehicleOptionSchema]:
        return self.service.list_vehicle_options()

    def list_location_options(self) -> list[LocationOptionSchema]:
        return self.service.list_location_options()

    def list_sale_options(self) -> list[SaleOptionSchema]:
        return self.service.list_sale_options()

    def list_lot_options(self) -> list[LotOptionSchema]:
        return self.service.list_lot_options()

    def list_driver_options(self) -> list[DriverOptionSchema]:
        return self.service.list_driver_options()

    def lookup_address_by_cep(self, cep: str) -> AddressLookupSchema:
        try:
            return self.service.lookup_address_by_cep(cep)
        except LogisticsError as exc:
            if "not found" in exc.message.lower():
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    exc.message,
                ) from exc
            raise self._map_error(exc) from exc

    # --- Vehicles ---

    def create_vehicle(self, payload: VehicleCreateSchema) -> VehicleReadSchema:
        try:
            return self.service.create_vehicle(payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc

    def list_vehicles(self) -> list[VehicleReadSchema]:
        return self.service.list_vehicles()

    def get_vehicle(self, vehicle_id: int) -> VehicleReadSchema:
        record = self.service.get_vehicle(vehicle_id)
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
        return record

    def update_vehicle(
        self, vehicle_id: int, payload: VehicleUpdateSchema
    ) -> VehicleReadSchema:
        try:
            record = self.service.update_vehicle(vehicle_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
        return record

    def delete_vehicle(self, vehicle_id: int) -> None:
        try:
            ok = self.service.delete_vehicle(vehicle_id)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")

    # --- Locations ---

    def create_location(self, payload: LocationCreateSchema) -> LocationReadSchema:
        try:
            return self.service.create_location(payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc

    def list_locations(self) -> list[LocationReadSchema]:
        return self.service.list_locations()

    def get_location(self, location_id: int) -> LocationReadSchema:
        record = self.service.get_location(location_id)
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
        return record

    def update_location(
        self, location_id: int, payload: LocationUpdateSchema
    ) -> LocationReadSchema:
        try:
            record = self.service.update_location(location_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")
        return record

    def delete_location(self, location_id: int) -> None:
        try:
            ok = self.service.delete_location(location_id)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Location not found")

    # --- Operations ---

    def create_operation(self, payload: OperationCreateSchema) -> OperationReadSchema:
        try:
            return self.service.create_operation(payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc

    def list_operations(self) -> list[OperationReadSchema]:
        return self.service.list_operations()

    def get_operation(self, operation_id: int) -> OperationReadSchema:
        record = self.service.get_operation(operation_id)
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operation not found")
        return record

    def update_operation(
        self, operation_id: int, payload: OperationUpdateSchema
    ) -> OperationReadSchema:
        try:
            record = self.service.update_operation(operation_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operation not found")
        return record

    def delete_operation(self, operation_id: int) -> None:
        if not self.service.delete_operation(operation_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operation not found")

    # --- Loads ---

    def list_all_loads(self) -> list[LoadReadSchema]:
        return self.service.list_all_loads()

    def get_load(self, load_id: int) -> LoadReadSchema:
        record = self.service.get_load(load_id)
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Load not found")
        return record

    def add_load(
        self, operation_id: int, payload: LoadCreateSchema
    ) -> LoadReadSchema:
        try:
            record = self.service.add_load(operation_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operation not found")
        return record

    def list_loads(self, operation_id: int) -> list[LoadReadSchema]:
        records = self.service.list_loads(operation_id)
        if records is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operation not found")
        return records

    def update_load(
        self, operation_id: int, load_id: int, payload: LoadUpdateSchema
    ) -> LoadReadSchema:
        try:
            record = self.service.update_load(operation_id, load_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Load not found")
        return record

    def delete_load(self, operation_id: int, load_id: int) -> None:
        try:
            ok = self.service.delete_load(operation_id, load_id)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Load not found")

    # --- Weighings ---

    def add_weighing(
        self, operation_id: int, load_id: int, payload: WeighingCreateSchema
    ) -> WeighingReadSchema:
        try:
            record = self.service.add_weighing(operation_id, load_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Load not found")
        return record

    def list_weighings(
        self, operation_id: int, load_id: int
    ) -> list[WeighingReadSchema]:
        try:
            records = self.service.list_weighings(operation_id, load_id)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if records is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Load not found")
        return records

    def update_weighing(
        self,
        operation_id: int,
        load_id: int,
        weighing_id: int,
        payload: WeighingUpdateSchema,
    ) -> WeighingReadSchema:
        try:
            record = self.service.update_weighing(
                operation_id, load_id, weighing_id, payload
            )
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Weighing not found")
        return record

    def delete_weighing(
        self, operation_id: int, load_id: int, weighing_id: int
    ) -> None:
        try:
            ok = self.service.delete_weighing(operation_id, load_id, weighing_id)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Weighing not found")

    # --- Dispatch ---

    def create_dispatch(
        self, operation_id: int, load_id: int, payload: DispatchCreateSchema
    ) -> DispatchReadSchema:
        try:
            record = self.service.create_dispatch(operation_id, load_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Load not found")
        return record

    def get_dispatch(self, operation_id: int, load_id: int) -> DispatchReadSchema:
        record = self.service.get_dispatch(operation_id, load_id)
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispatch not found")
        return record

    def update_dispatch(
        self, operation_id: int, load_id: int, payload: DispatchUpdateSchema
    ) -> DispatchReadSchema:
        try:
            record = self.service.update_dispatch(operation_id, load_id, payload)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if record is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispatch not found")
        return record

    def delete_dispatch(self, operation_id: int, load_id: int) -> None:
        try:
            ok = self.service.delete_dispatch(operation_id, load_id)
        except LogisticsError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispatch not found")


logistics_controller = LogisticsController()
router = logistics_controller.router
