"""HTTP client for the phytosanitary Streamlit UI → FastAPI."""

from __future__ import annotations

import requests

from app.core.config import settings
from app.fitossanidade.schemas.agent_occurrence import (
    AgentOccurrenceCreateSchema,
    AgentOccurrenceReadSchema,
    AgentOccurrenceUpdateSchema,
)
from app.fitossanidade.schemas.control import (
    ControlCreateSchema,
    ControlReadSchema,
    ControlUpdateSchema,
)
from app.fitossanidade.schemas.harmful_agent import (
    DiseaseCreateSchema,
    HarmfulAgentReadSchema,
    HarmfulAgentUpdateSchema,
    PestCreateSchema,
)
from app.fitossanidade.schemas.lookups import (
    AgentOptionSchema,
    EmployeeOptionSchema,
    InputOptionSchema,
    MachineOptionSchema,
    PlantingOptionSchema,
)
from app.fitossanidade.schemas.pesticide_application import (
    PesticideApplicationCreateSchema,
    PesticideApplicationReadSchema,
    PesticideApplicationUpdateSchema,
)


# API returns English details; Streamlit must show Portuguese to the user.
_API_DETAIL_TO_PT: tuple[tuple[str, str], ...] = (
    ("id_plantio, id_funcionario and id_agente exist", "Verifique plantio, funcionario e agentes."),
    ("id_plantio and id_funcionario exist", "Verifique se o plantio e o funcionario existem."),
    ("id_agente exists", "Verifique se o agente nocivo existe."),
    ("id_insumo exists", "Verifique se o insumo (defensivo) existe."),
    ("Harmful agent not found", "Agente nocivo nao encontrado."),
    ("Input (insumo) not found", "Insumo nao encontrado."),
    ("Input is not a pesticide", "Selecione um defensivo (nao fertilizante/semente)."),
    ("Insufficient stock for pesticide", "Estoque insuficiente para a aplicacao de defensivo."),
    ("Machine not found", "Maquina nao encontrada."),
    ("linked to control occurrences", "Nao e possivel excluir agente vinculado a ocorrencias."),
    ("dt_carencia must be on or after", "A data de carencia deve ser igual ou posterior a aplicacao."),
    ("Could not create pest", "Nao foi possivel cadastrar a praga."),
    ("Could not create disease", "Nao foi possivel cadastrar a doenca."),
    ("Could not create control", "Nao foi possivel criar o controle fitossanitario."),
    ("Could not update control", "Nao foi possivel atualizar o controle."),
    ("Could not add occurrence", "Nao foi possivel adicionar a ocorrencia."),
    ("Could not update occurrence", "Nao foi possivel atualizar a ocorrencia."),
    ("Could not add application", "Nao foi possivel registrar a aplicacao."),
    ("Could not update application", "Nao foi possivel atualizar a aplicacao."),
    ("Could not reverse stock", "Nao foi possivel estornar o estoque da aplicacao."),
    ("Control not found", "Controle fitossanitario nao encontrado."),
    ("Occurrence not found", "Ocorrencia nao encontrada."),
    ("Application not found", "Aplicacao de defensivo nao encontrada."),
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


class PhytosanitaryApiError(Exception):
    """Raised when the phytosanitary API returns an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.user_message = _to_user_message(message, status_code)
        super().__init__(message)


class PhytosanitaryClient:
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
        raise PhytosanitaryApiError(detail, status_code=response.status_code)

    # --- Lookups ---

    def list_plantings(self) -> list[PlantingOptionSchema]:
        response = requests.get(
            self._url("/phytosanitary/lookups/plantings"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [PlantingOptionSchema.model_validate(item) for item in response.json()]

    def list_employees(self) -> list[EmployeeOptionSchema]:
        response = requests.get(
            self._url("/phytosanitary/lookups/employees"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [EmployeeOptionSchema.model_validate(item) for item in response.json()]

    def list_inputs(self) -> list[InputOptionSchema]:
        response = requests.get(
            self._url("/phytosanitary/lookups/inputs"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [InputOptionSchema.model_validate(item) for item in response.json()]

    def list_machines(self) -> list[MachineOptionSchema]:
        response = requests.get(
            self._url("/phytosanitary/lookups/machines"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [MachineOptionSchema.model_validate(item) for item in response.json()]

    def list_agent_options(self) -> list[AgentOptionSchema]:
        response = requests.get(
            self._url("/phytosanitary/lookups/agents"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [AgentOptionSchema.model_validate(item) for item in response.json()]

    # --- Agents ---

    def list_agents(self) -> list[HarmfulAgentReadSchema]:
        response = requests.get(self._url("/phytosanitary/agents"), timeout=self.timeout)
        self._raise_for_api(response)
        return [HarmfulAgentReadSchema.model_validate(item) for item in response.json()]

    def get_agent(self, agent_id: int) -> HarmfulAgentReadSchema:
        response = requests.get(
            self._url(f"/phytosanitary/agents/{agent_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return HarmfulAgentReadSchema.model_validate(response.json())

    def create_pest(self, payload: PestCreateSchema) -> HarmfulAgentReadSchema:
        response = requests.post(
            self._url("/phytosanitary/agents/pests"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return HarmfulAgentReadSchema.model_validate(response.json())

    def create_disease(self, payload: DiseaseCreateSchema) -> HarmfulAgentReadSchema:
        response = requests.post(
            self._url("/phytosanitary/agents/diseases"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return HarmfulAgentReadSchema.model_validate(response.json())

    def update_agent(
        self, agent_id: int, payload: HarmfulAgentUpdateSchema
    ) -> HarmfulAgentReadSchema:
        response = requests.patch(
            self._url(f"/phytosanitary/agents/{agent_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return HarmfulAgentReadSchema.model_validate(response.json())

    def delete_agent(self, agent_id: int) -> None:
        response = requests.delete(
            self._url(f"/phytosanitary/agents/{agent_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- Controls ---

    def list_controls(self) -> list[ControlReadSchema]:
        response = requests.get(
            self._url("/phytosanitary/controls"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [ControlReadSchema.model_validate(item) for item in response.json()]

    def get_control(self, control_id: int) -> ControlReadSchema:
        response = requests.get(
            self._url(f"/phytosanitary/controls/{control_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return ControlReadSchema.model_validate(response.json())

    def create_control(self, payload: ControlCreateSchema) -> ControlReadSchema:
        response = requests.post(
            self._url("/phytosanitary/controls"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ControlReadSchema.model_validate(response.json())

    def update_control(
        self, control_id: int, payload: ControlUpdateSchema
    ) -> ControlReadSchema:
        response = requests.patch(
            self._url(f"/phytosanitary/controls/{control_id}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ControlReadSchema.model_validate(response.json())

    def delete_control(self, control_id: int) -> None:
        response = requests.delete(
            self._url(f"/phytosanitary/controls/{control_id}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- Occurrences ---

    def list_occurrences(self, control_id: int) -> list[AgentOccurrenceReadSchema]:
        response = requests.get(
            self._url(f"/phytosanitary/controls/{control_id}/occurrences"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [
            AgentOccurrenceReadSchema.model_validate(item) for item in response.json()
        ]

    def add_occurrence(
        self, control_id: int, payload: AgentOccurrenceCreateSchema
    ) -> AgentOccurrenceReadSchema:
        response = requests.post(
            self._url(f"/phytosanitary/controls/{control_id}/occurrences"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return AgentOccurrenceReadSchema.model_validate(response.json())

    def update_occurrence(
        self,
        control_id: int,
        occurrence_id: int,
        payload: AgentOccurrenceUpdateSchema,
    ) -> AgentOccurrenceReadSchema:
        response = requests.patch(
            self._url(
                f"/phytosanitary/controls/{control_id}/occurrences/{occurrence_id}"
            ),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return AgentOccurrenceReadSchema.model_validate(response.json())

    def delete_occurrence(self, control_id: int, occurrence_id: int) -> None:
        response = requests.delete(
            self._url(
                f"/phytosanitary/controls/{control_id}/occurrences/{occurrence_id}"
            ),
            timeout=self.timeout,
        )
        self._raise_for_api(response)

    # --- Applications ---

    def list_applications(
        self, control_id: int
    ) -> list[PesticideApplicationReadSchema]:
        response = requests.get(
            self._url(f"/phytosanitary/controls/{control_id}/applications"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [
            PesticideApplicationReadSchema.model_validate(item)
            for item in response.json()
        ]

    def add_application(
        self, control_id: int, payload: PesticideApplicationCreateSchema
    ) -> PesticideApplicationReadSchema:
        response = requests.post(
            self._url(f"/phytosanitary/controls/{control_id}/applications"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return PesticideApplicationReadSchema.model_validate(response.json())

    def update_application(
        self,
        control_id: int,
        application_id: int,
        payload: PesticideApplicationUpdateSchema,
    ) -> PesticideApplicationReadSchema:
        response = requests.patch(
            self._url(
                f"/phytosanitary/controls/{control_id}/applications/{application_id}"
            ),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return PesticideApplicationReadSchema.model_validate(response.json())

    def delete_application(self, control_id: int, application_id: int) -> None:
        response = requests.delete(
            self._url(
                f"/phytosanitary/controls/{control_id}/applications/{application_id}"
            ),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
