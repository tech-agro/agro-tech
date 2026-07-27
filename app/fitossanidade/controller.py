"""HTTP adapter for the phytosanitary domain."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.fitossanidade.errors import PhytosanitaryError
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
from app.fitossanidade.service import PhytosanitaryService


class PhytosanitaryController:
    """Exposes agents and controls; occurrences/applications nest under control."""

    def __init__(self, service: PhytosanitaryService | None = None) -> None:
        self.service = service or PhytosanitaryService()
        self.router = APIRouter(prefix="/phytosanitary", tags=["phytosanitary"])
        self._register_routes()

    @staticmethod
    def _map_error(exc: PhytosanitaryError) -> HTTPException:
        return HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    def _register_routes(self) -> None:
        self.router.get(
            "/lookups/plantings", response_model=list[PlantingOptionSchema]
        )(self.list_planting_options)
        self.router.get(
            "/lookups/employees", response_model=list[EmployeeOptionSchema]
        )(self.list_employee_options)
        self.router.get("/lookups/inputs", response_model=list[InputOptionSchema])(
            self.list_input_options
        )
        self.router.get("/lookups/machines", response_model=list[MachineOptionSchema])(
            self.list_machine_options
        )
        self.router.get("/lookups/agents", response_model=list[AgentOptionSchema])(
            self.list_agent_options
        )

        self.router.post("/agents/pests", response_model=HarmfulAgentReadSchema)(
            self.create_pest
        )
        self.router.post("/agents/diseases", response_model=HarmfulAgentReadSchema)(
            self.create_disease
        )
        self.router.get("/agents", response_model=list[HarmfulAgentReadSchema])(
            self.list_agents
        )
        self.router.get("/agents/{agent_id}", response_model=HarmfulAgentReadSchema)(
            self.get_agent
        )
        self.router.patch("/agents/{agent_id}", response_model=HarmfulAgentReadSchema)(
            self.update_agent
        )
        self.router.delete(
            "/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_agent)

        self.router.post("/controls", response_model=ControlReadSchema)(
            self.create_control
        )
        self.router.get("/controls", response_model=list[ControlReadSchema])(
            self.list_controls
        )
        self.router.get("/controls/{control_id}", response_model=ControlReadSchema)(
            self.get_control
        )
        self.router.patch("/controls/{control_id}", response_model=ControlReadSchema)(
            self.update_control
        )
        self.router.delete(
            "/controls/{control_id}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_control)

        self.router.post(
            "/controls/{control_id}/occurrences",
            response_model=AgentOccurrenceReadSchema,
        )(self.add_occurrence)
        self.router.get(
            "/controls/{control_id}/occurrences",
            response_model=list[AgentOccurrenceReadSchema],
        )(self.list_occurrences)
        self.router.patch(
            "/controls/{control_id}/occurrences/{occurrence_id}",
            response_model=AgentOccurrenceReadSchema,
        )(self.update_occurrence)
        self.router.delete(
            "/controls/{control_id}/occurrences/{occurrence_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_occurrence)

        self.router.post(
            "/controls/{control_id}/applications",
            response_model=PesticideApplicationReadSchema,
        )(self.add_application)
        self.router.get(
            "/controls/{control_id}/applications",
            response_model=list[PesticideApplicationReadSchema],
        )(self.list_applications)
        self.router.patch(
            "/controls/{control_id}/applications/{application_id}",
            response_model=PesticideApplicationReadSchema,
        )(self.update_application)
        self.router.delete(
            "/controls/{control_id}/applications/{application_id}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_application)

    def list_planting_options(self) -> list[PlantingOptionSchema]:
        return self.service.list_planting_options()

    def list_employee_options(self) -> list[EmployeeOptionSchema]:
        return self.service.list_employee_options()

    def list_input_options(self) -> list[InputOptionSchema]:
        return self.service.list_input_options()

    def list_machine_options(self) -> list[MachineOptionSchema]:
        return self.service.list_machine_options()

    def list_agent_options(self) -> list[AgentOptionSchema]:
        return self.service.list_agent_options()

    def create_pest(self, payload: PestCreateSchema) -> HarmfulAgentReadSchema:
        try:
            return self.service.create_pest(payload)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc

    def create_disease(self, payload: DiseaseCreateSchema) -> HarmfulAgentReadSchema:
        try:
            return self.service.create_disease(payload)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc

    def list_agents(self) -> list[HarmfulAgentReadSchema]:
        return self.service.list_agents()

    def get_agent(self, agent_id: int) -> HarmfulAgentReadSchema:
        agent = self.service.get_agent(agent_id)
        if agent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Harmful agent not found")
        return agent

    def update_agent(
        self, agent_id: int, payload: HarmfulAgentUpdateSchema
    ) -> HarmfulAgentReadSchema:
        agent = self.service.update_agent(agent_id, payload)
        if agent is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Harmful agent not found")
        return agent

    def delete_agent(self, agent_id: int) -> None:
        try:
            ok = self.service.delete_agent(agent_id)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Harmful agent not found")

    def create_control(self, payload: ControlCreateSchema) -> ControlReadSchema:
        try:
            return self.service.create_control(payload)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc

    def list_controls(self) -> list[ControlReadSchema]:
        return self.service.list_controls()

    def get_control(self, control_id: int) -> ControlReadSchema:
        control = self.service.get_control(control_id)
        if control is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
        return control

    def update_control(
        self, control_id: int, payload: ControlUpdateSchema
    ) -> ControlReadSchema:
        try:
            control = self.service.update_control(control_id, payload)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if control is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
        return control

    def delete_control(self, control_id: int) -> None:
        try:
            ok = self.service.delete_control(control_id)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")

    def add_occurrence(
        self, control_id: int, payload: AgentOccurrenceCreateSchema
    ) -> AgentOccurrenceReadSchema:
        try:
            occurrence = self.service.add_occurrence(control_id, payload)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if occurrence is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
        return occurrence

    def list_occurrences(self, control_id: int) -> list[AgentOccurrenceReadSchema]:
        occurrences = self.service.list_occurrences(control_id)
        if occurrences is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
        return occurrences

    def update_occurrence(
        self,
        control_id: int,
        occurrence_id: int,
        payload: AgentOccurrenceUpdateSchema,
    ) -> AgentOccurrenceReadSchema:
        try:
            occurrence = self.service.update_occurrence(
                control_id, occurrence_id, payload
            )
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if occurrence is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Occurrence not found")
        return occurrence

    def delete_occurrence(self, control_id: int, occurrence_id: int) -> None:
        if not self.service.delete_occurrence(control_id, occurrence_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Occurrence not found")

    def add_application(
        self, control_id: int, payload: PesticideApplicationCreateSchema
    ) -> PesticideApplicationReadSchema:
        try:
            application = self.service.add_application(control_id, payload)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if application is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
        return application

    def list_applications(
        self, control_id: int
    ) -> list[PesticideApplicationReadSchema]:
        applications = self.service.list_applications(control_id)
        if applications is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Control not found")
        return applications

    def update_application(
        self,
        control_id: int,
        application_id: int,
        payload: PesticideApplicationUpdateSchema,
    ) -> PesticideApplicationReadSchema:
        try:
            application = self.service.update_application(
                control_id, application_id, payload
            )
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if application is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
        return application

    def delete_application(self, control_id: int, application_id: int) -> None:
        try:
            ok = self.service.delete_application(control_id, application_id)
        except PhytosanitaryError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")


phytosanitary_controller = PhytosanitaryController()
router = phytosanitary_controller.router
