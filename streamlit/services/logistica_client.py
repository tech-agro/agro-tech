"""HTTP client for the logistics Streamlit UI → FastAPI."""

from __future__ import annotations

from urllib.parse import quote

import requests

from app.core.config import settings
from app.logistica.schemas.address import AddressLookupSchema
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


_API_DETAIL_TO_PT: tuple[tuple[str, str], ...] = (
    ("id_veiculo, id_origem", "Verifique veiculo, origem, destino, venda e lotes."),
    ("id_destino and id_venda exist", "Verifique veiculo, origem, destino e venda."),
    ("id_lote exists", "Verifique se o lote existe."),
    ("placa is unique", "Placa ja cadastrada."),
    ("Address not found", "Endereco nao encontrado."),
    ("Origin location not found", "Local de origem nao encontrado."),
    ("Destination location not found", "Local de destino nao encontrado."),
    ("Location not found", "Local nao encontrado."),
    ("does not allow load changes", "Esta operacao nao permite alterar cargas no status atual."),
    ("does not allow weighing or dispatch", "Esta operacao nao permite pesagem/expedicao no status atual."),
    ("already has a dispatch", "A carga ja possui expedicao (relacao 1:1)."),
    ("after it has been shipped or delivered", "Nao e possivel excluir expedicao ja expedida ou entregue."),
    ("linked to vehicles", "Nao e possivel excluir tipo vinculado a veiculos."),
    ("linked to operations", "Nao e possivel excluir registro vinculado a operacoes."),
    ("data_fim must be on or after", "A data fim deve ser igual ou posterior a data inicio."),
    ("origem and destino must be different", "Origem e destino devem ser diferentes."),
    ("nome+tipo is unique", "Ja existe local com este nome e tipo."),
    ("Driver not found", "Motorista nao encontrado."),
    ("Operation not found", "Operacao logistica nao encontrada."),
    ("Load not found", "Carga nao encontrada."),
    ("Weighing not found", "Pesagem nao encontrada."),
    ("Dispatch not found", "Expedicao nao encontrada."),
    ("Vehicle not found", "Veiculo nao encontrado."),
    ("CEP must contain exactly 8 digits.", "Informe um CEP valido com 8 digitos."),
    (
        "Nao foi possivel consultar o CEP no ViaCEP",
        "Nao foi possivel consultar o CEP. Tente novamente em instantes.",
    ),
    (
        "ViaCEP payload could not be mapped",
        "Resposta invalida do servico de CEP. Tente novamente.",
    ),
    ("not found", "CEP nao encontrado."),
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


class LogisticsApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.user_message = _to_user_message(message, status_code)
        super().__init__(message)


class LogisticsClient:
    def __init__(self, base_url: str | None = None, timeout: float = 15) -> None:
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _raise_for_api(self, response: requests.Response) -> None:
        if response.ok:
            return
        try:
            payload = response.json()
            detail = payload.get("detail", response.text)
            if isinstance(detail, list):
                parts: list[str] = []
                for item in detail:
                    if isinstance(item, dict):
                        parts.append(str(item.get("msg", item)))
                    else:
                        parts.append(str(item))
                detail = "; ".join(parts)
            else:
                detail = str(detail)
        except Exception:
            detail = response.text or response.reason
        raise LogisticsApiError(detail, status_code=response.status_code)

    # --- Lookups ---

    def list_vehicle_types_options(self) -> list[VehicleTypeOptionSchema]:
        response = requests.get(
            self._url("/logistics/lookups/vehicle-types"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [VehicleTypeOptionSchema.model_validate(i) for i in response.json()]

    def list_vehicles_options(self) -> list[VehicleOptionSchema]:
        response = requests.get(
            self._url("/logistics/lookups/vehicles"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [VehicleOptionSchema.model_validate(i) for i in response.json()]

    def list_locations_options(self) -> list[LocationOptionSchema]:
        response = requests.get(
            self._url("/logistics/lookups/locations"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [LocationOptionSchema.model_validate(i) for i in response.json()]

    def list_sales(self) -> list[SaleOptionSchema]:
        response = requests.get(
            self._url("/logistics/lookups/sales"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [SaleOptionSchema.model_validate(i) for i in response.json()]

    def list_lots(self) -> list[LotOptionSchema]:
        response = requests.get(
            self._url("/logistics/lookups/lots"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [LotOptionSchema.model_validate(i) for i in response.json()]

    def list_drivers(self) -> list[DriverOptionSchema]:
        response = requests.get(
            self._url("/logistics/lookups/drivers"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [DriverOptionSchema.model_validate(i) for i in response.json()]

    def lookup_address_by_cep(self, cep: str) -> AddressLookupSchema:
        encoded_cep = quote(cep.strip(), safe="")
        response = requests.get(
            self._url(f"/logistics/addresses/by-cep/{encoded_cep}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return AddressLookupSchema.model_validate(response.json())

    # --- Vehicles ---

    def create_vehicle(self, payload: VehicleCreateSchema) -> VehicleReadSchema:
        response = requests.post(
            self._url("/logistics/vehicles"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return VehicleReadSchema.model_validate(response.json())

    def list_vehicles(self) -> list[VehicleReadSchema]:
        response = requests.get(self._url("/logistics/vehicles"), timeout=self.timeout)
        self._raise_for_api(response)
        return [VehicleReadSchema.model_validate(i) for i in response.json()]

    def get_vehicle(self, vehicle_id: int) -> VehicleReadSchema:
        response = requests.get(
            self._url(f"/logistics/vehicles/{vehicle_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return VehicleReadSchema.model_validate(response.json())

    def update_vehicle(
        self, vehicle_id: int, payload: VehicleUpdateSchema
    ) -> VehicleReadSchema:
        response = requests.patch(
            self._url(f"/logistics/vehicles/{vehicle_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return VehicleReadSchema.model_validate(response.json())

    def delete_vehicle(self, vehicle_id: int) -> None:
        response = requests.delete(
            self._url(f"/logistics/vehicles/{vehicle_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    def create_location(self, payload: LocationCreateSchema) -> LocationReadSchema:
        response = requests.post(
            self._url("/logistics/locations"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return LocationReadSchema.model_validate(response.json())

    def list_locations(self) -> list[LocationReadSchema]:
        response = requests.get(self._url("/logistics/locations"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LocationReadSchema.model_validate(i) for i in response.json()]

    def get_location(self, location_id: int) -> LocationReadSchema:
        response = requests.get(
            self._url(f"/logistics/locations/{location_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return LocationReadSchema.model_validate(response.json())

    def update_location(
        self, location_id: int, payload: LocationUpdateSchema
    ) -> LocationReadSchema:
        response = requests.patch(
            self._url(f"/logistics/locations/{location_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return LocationReadSchema.model_validate(response.json())

    def delete_location(self, location_id: int) -> None:
        response = requests.delete(
            self._url(f"/logistics/locations/{location_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- Operations ---

    def list_operations(self) -> list[OperationReadSchema]:
        response = requests.get(self._url("/logistics/operations"), timeout=self.timeout)
        self._raise_for_api(response)
        return [OperationReadSchema.model_validate(i) for i in response.json()]

    def get_operation(self, operation_id: int) -> OperationReadSchema:
        response = requests.get(
            self._url(f"/logistics/operations/{operation_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return OperationReadSchema.model_validate(response.json())

    def create_operation(self, payload: OperationCreateSchema) -> OperationReadSchema:
        response = requests.post(
            self._url("/logistics/operations"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return OperationReadSchema.model_validate(response.json())

    def update_operation(
        self, operation_id: int, payload: OperationUpdateSchema
    ) -> OperationReadSchema:
        response = requests.patch(
            self._url(f"/logistics/operations/{operation_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return OperationReadSchema.model_validate(response.json())

    def delete_operation(self, operation_id: int) -> None:
        response = requests.delete(
            self._url(f"/logistics/operations/{operation_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- Loads ---

    def list_all_loads(self) -> list[LoadReadSchema]:
        response = requests.get(self._url("/logistics/loads"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LoadReadSchema.model_validate(i) for i in response.json()]

    def get_load(self, load_id: int) -> LoadReadSchema:
        response = requests.get(
            self._url(f"/logistics/loads/{load_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return LoadReadSchema.model_validate(response.json())

    def list_loads(self, operation_id: int) -> list[LoadReadSchema]:
        response = requests.get(
            self._url(f"/logistics/operations/{operation_id}/loads"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [LoadReadSchema.model_validate(i) for i in response.json()]

    def add_load(self, operation_id: int, payload: LoadCreateSchema) -> LoadReadSchema:
        response = requests.post(
            self._url(f"/logistics/operations/{operation_id}/loads"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return LoadReadSchema.model_validate(response.json())

    def update_load(
        self, operation_id: int, load_id: int, payload: LoadUpdateSchema
    ) -> LoadReadSchema:
        response = requests.patch(
            self._url(f"/logistics/operations/{operation_id}/loads/{load_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return LoadReadSchema.model_validate(response.json())

    def delete_load(self, operation_id: int, load_id: int) -> None:
        response = requests.delete(
            self._url(f"/logistics/operations/{operation_id}/loads/{load_id}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)

    # --- Weighings ---

    def list_weighings(self, operation_id: int, load_id: int) -> list[WeighingReadSchema]:
        response = requests.get(
            self._url(
                f"/logistics/operations/{operation_id}/loads/{load_id}/weighings"
            ),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [WeighingReadSchema.model_validate(i) for i in response.json()]

    def add_weighing(
        self, operation_id: int, load_id: int, payload: WeighingCreateSchema
    ) -> WeighingReadSchema:
        response = requests.post(
            self._url(
                f"/logistics/operations/{operation_id}/loads/{load_id}/weighings"
            ),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return WeighingReadSchema.model_validate(response.json())

    def update_weighing(
        self,
        operation_id: int,
        load_id: int,
        weighing_id: int,
        payload: WeighingUpdateSchema,
    ) -> WeighingReadSchema:
        response = requests.patch(
            self._url(
                f"/logistics/operations/{operation_id}/loads/{load_id}/weighings/{weighing_id}"
            ),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return WeighingReadSchema.model_validate(response.json())

    def delete_weighing(
        self, operation_id: int, load_id: int, weighing_id: int
    ) -> None:
        response = requests.delete(
            self._url(
                f"/logistics/operations/{operation_id}/loads/{load_id}/weighings/{weighing_id}"
            ),
            timeout=self.timeout,
        )
        self._raise_for_api(response)

    # --- Dispatch ---

    def get_dispatch(self, operation_id: int, load_id: int) -> DispatchReadSchema | None:
        response = requests.get(
            self._url(
                f"/logistics/operations/{operation_id}/loads/{load_id}/dispatch"
            ),
            timeout=self.timeout,
        )
        if response.status_code == 404:
            return None
        self._raise_for_api(response)
        return DispatchReadSchema.model_validate(response.json())

    def create_dispatch(
        self, operation_id: int, load_id: int, payload: DispatchCreateSchema
    ) -> DispatchReadSchema:
        response = requests.post(
            self._url(
                f"/logistics/operations/{operation_id}/loads/{load_id}/dispatch"
            ),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return DispatchReadSchema.model_validate(response.json())

    def update_dispatch(
        self, operation_id: int, load_id: int, payload: DispatchUpdateSchema
    ) -> DispatchReadSchema:
        response = requests.patch(
            self._url(
                f"/logistics/operations/{operation_id}/loads/{load_id}/dispatch"
            ),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return DispatchReadSchema.model_validate(response.json())
