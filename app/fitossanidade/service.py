"""Phytosanitary domain use cases."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.database import get_session
from app.fitossanidade.enum import SEVERITY_RANK, AgentKind
from app.fitossanidade.errors import PhytosanitaryError
from app.fitossanidade.models.agent_occurrence import AgentOccurrenceModel
from app.fitossanidade.models.control import ControlModel
from app.fitossanidade.models.disease import DiseaseModel
from app.fitossanidade.models.harmful_agent import HarmfulAgentModel
from app.fitossanidade.models.pest import PestModel
from app.fitossanidade.repository import (
    AgentOccurrenceRepository,
    ControlRepository,
    DiseaseRepository,
    HarmfulAgentRepository,
    PestRepository,
    PesticideApplicationRepository,
    PhytosanitaryLookupRepository,
)
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


class PhytosanitaryService:
    """Orchestrates agents, controls, occurrences, and pesticide applications."""

    def __init__(
        self,
        agent_repo: HarmfulAgentRepository | None = None,
        pest_repo: PestRepository | None = None,
        disease_repo: DiseaseRepository | None = None,
        control_repo: ControlRepository | None = None,
        occurrence_repo: AgentOccurrenceRepository | None = None,
        application_repo: PesticideApplicationRepository | None = None,
        lookup_repo: PhytosanitaryLookupRepository | None = None,
    ) -> None:
        self.agent_repo = agent_repo or HarmfulAgentRepository()
        self.pest_repo = pest_repo or PestRepository()
        self.disease_repo = disease_repo or DiseaseRepository()
        self.control_repo = control_repo or ControlRepository()
        self.occurrence_repo = occurrence_repo or AgentOccurrenceRepository()
        self.application_repo = application_repo or PesticideApplicationRepository()
        self.lookup_repo = lookup_repo or PhytosanitaryLookupRepository()

    @staticmethod
    def _to_agent_read(
        agent: HarmfulAgentModel,
        kind: AgentKind,
        pest: PestModel | None,
        disease: DiseaseModel | None,
    ) -> HarmfulAgentReadSchema:
        return HarmfulAgentReadSchema(
            id_agente=agent.id_agente,
            nome_comum=agent.nome_comum,
            nome_cientifico=agent.nome_cientifico,
            kind=kind,
            tipo_praga=pest.tipo_praga if pest else None,
            habito_alimentar=pest.habito_alimentar if pest else None,
            agente_causador=disease.agente_causador if disease else None,
            sintomas=disease.sintomas if disease else None,
            condicao_favoravel=disease.condicao_favoravel if disease else None,
        )

    @staticmethod
    def _to_control_read(
        control: ControlModel,
        plantio_produto_nome: str | None,
        funcionario_nome: str | None,
    ) -> ControlReadSchema:
        data = ControlReadSchema.model_validate(control).model_dump()
        data["plantio_produto_nome"] = plantio_produto_nome
        data["funcionario_nome"] = funcionario_nome
        return ControlReadSchema.model_validate(data)

    @staticmethod
    def _to_occurrence_read(
        occurrence: AgentOccurrenceModel, agente_nome: str | None
    ) -> AgentOccurrenceReadSchema:
        data = AgentOccurrenceReadSchema.model_validate(occurrence).model_dump()
        data["agente_nome"] = agente_nome
        return AgentOccurrenceReadSchema.model_validate(data)

    @staticmethod
    def _to_application_read(
        application, insumo_nome: str | None, maquina_nome: str | None = None
    ) -> PesticideApplicationReadSchema:
        data = PesticideApplicationReadSchema.model_validate(application).model_dump()
        data["insumo_nome"] = insumo_nome
        data["maquina_nome"] = maquina_nome
        return PesticideApplicationReadSchema.model_validate(data)

    @staticmethod
    def _aggregate_severity(levels: list[str | None]) -> str | None:
        best: str | None = None
        best_rank = 0
        for level in levels:
            if not level:
                continue
            rank = SEVERITY_RANK.get(level, 0)
            if rank > best_rank:
                best = level
                best_rank = rank
        return best

    def _refresh_control_severity(self, control_id: int) -> None:
        """Derive control severity from the worst infestation among occurrences."""
        occurrences = self.occurrence_repo.list(filters={"id_controle": control_id})
        aggregated = self._aggregate_severity(
            [occurrence.nivel_infestacao for occurrence in occurrences]
        )
        self.control_repo.update(control_id, {"nivel_severidade": aggregated})

    def _load_agent_read(self, agent_id: int) -> HarmfulAgentReadSchema | None:
        loaded = self.agent_repo.get_with_kind(agent_id)
        if loaded is None:
            return None
        agent, kind, pest, disease = loaded
        return self._to_agent_read(agent, kind, pest, disease)

    def _load_control_read(self, control_id: int) -> ControlReadSchema | None:
        loaded = self.control_repo.get_with_labels(control_id)
        if loaded is None:
            return None
        control, produto_nome, funcionario_nome = loaded
        return self._to_control_read(control, produto_nome, funcionario_nome)

    def _load_occurrence_read(
        self, occurrence_id: int
    ) -> AgentOccurrenceReadSchema | None:
        loaded = self.occurrence_repo.get_with_agent_name(occurrence_id)
        if loaded is None:
            return None
        occurrence, nome = loaded
        return self._to_occurrence_read(occurrence, nome)

    def _load_application_read(
        self, application_id: int
    ) -> PesticideApplicationReadSchema | None:
        loaded = self.application_repo.get_with_input_name(application_id)
        if loaded is None:
            return None
        application, nome, maquina_nome = loaded
        return self._to_application_read(application, nome, maquina_nome)

    def _assert_withdrawal_dates(
        self, dt_aplicacao, dt_carencia, *, id_insumo: int | None = None
    ) -> None:
        if (
            dt_carencia is not None
            and dt_aplicacao is not None
            and dt_carencia < dt_aplicacao
        ):
            raise PhytosanitaryError("dt_carencia must be on or after dt_aplicacao")
        if id_insumo is not None and self.lookup_repo.get_input(id_insumo) is None:
            raise PhytosanitaryError("Input (insumo) not found")

    def _assert_pesticide_input(self, id_insumo: int) -> None:
        if self.lookup_repo.get_input(id_insumo) is None:
            raise PhytosanitaryError("Input (insumo) not found")
        if not self.lookup_repo.is_pesticide_input(id_insumo):
            raise PhytosanitaryError(
                "Input is not a pesticide (defensivo); only defensive inputs are allowed"
            )

    def _assert_machine(self, id_maquina: int | None) -> None:
        if id_maquina is None:
            return
        if self.lookup_repo.get_machine(id_maquina) is None:
            raise PhytosanitaryError("Machine not found")

    def _resolve_withdrawal_date(
        self, id_insumo: int, dt_aplicacao, dt_carencia
    ):
        if dt_carencia is not None:
            return dt_carencia
        return self.lookup_repo.compute_withdrawal_date(id_insumo, dt_aplicacao)

    # --- Lookups ---

    def list_planting_options(self) -> list[PlantingOptionSchema]:
        return [
            PlantingOptionSchema(
                id_plantio=plantio.id_plantio,
                produto_nome=nome,
                dt_plantio=plantio.dt_plantio,
            )
            for plantio, nome in self.lookup_repo.list_plantings()
        ]

    def list_employee_options(self) -> list[EmployeeOptionSchema]:
        return [
            EmployeeOptionSchema(
                id_funcionario=funcionario.id_funcionario,
                nome=nome,
                cargo=funcionario.cargo,
                setor=funcionario.setor,
            )
            for funcionario, nome in self.lookup_repo.list_employees()
        ]

    def list_input_options(self) -> list[InputOptionSchema]:
        return [
            InputOptionSchema(
                id_insumo=insumo.id_produto,
                nome=nome,
                classe_agronomica=insumo.classe_agronomica,
                principio_ativo=insumo.principio_ativo,
                periodo_carencia_dias=insumo.periodo_carencia_dias,
            )
            for insumo, nome in self.lookup_repo.list_inputs()
        ]

    def list_agent_options(self) -> list[AgentOptionSchema]:
        return [
            AgentOptionSchema(
                id_agente=agent.id_agente,
                nome_comum=agent.nome_comum,
                nome_cientifico=agent.nome_cientifico,
                kind=kind.value,
            )
            for agent, kind, _pest, _disease in self.agent_repo.list_with_kind()
        ]

    def list_machine_options(self) -> list[MachineOptionSchema]:
        return [
            MachineOptionSchema(
                id_maquina=machine.id_maquina,
                nome=machine.nome,
                status=machine.status,
            )
            for machine in self.lookup_repo.list_machines()
        ]

    # --- Harmful agents (pest / disease specialization) ---

    def create_pest(self, payload: PestCreateSchema) -> HarmfulAgentReadSchema:
        """Create agente_nocivo + praga in one transaction (disjoint specialization)."""
        try:
            with get_session() as session:
                agent = HarmfulAgentModel(
                    nome_comum=payload.nome_comum,
                    nome_cientifico=payload.nome_cientifico,
                )
                session.add(agent)
                session.flush()
                agent_id = agent.id_agente
                session.add(
                    PestModel(
                        id_agente=agent_id,
                        tipo_praga=payload.tipo_praga,
                        habito_alimentar=payload.habito_alimentar,
                    )
                )
                session.flush()
        except IntegrityError as exc:
            raise PhytosanitaryError("Could not create pest") from exc
        loaded = self._load_agent_read(agent_id)
        assert loaded is not None
        return loaded

    def create_disease(self, payload: DiseaseCreateSchema) -> HarmfulAgentReadSchema:
        """Create agente_nocivo + doenca in one transaction (disjoint specialization)."""
        try:
            with get_session() as session:
                agent = HarmfulAgentModel(
                    nome_comum=payload.nome_comum,
                    nome_cientifico=payload.nome_cientifico,
                )
                session.add(agent)
                session.flush()
                agent_id = agent.id_agente
                session.add(
                    DiseaseModel(
                        id_agente=agent_id,
                        agente_causador=payload.agente_causador,
                        sintomas=payload.sintomas,
                        condicao_favoravel=payload.condicao_favoravel,
                    )
                )
                session.flush()
        except IntegrityError as exc:
            raise PhytosanitaryError("Could not create disease") from exc
        loaded = self._load_agent_read(agent_id)
        assert loaded is not None
        return loaded

    def list_agents(self) -> list[HarmfulAgentReadSchema]:
        return [
            self._to_agent_read(agent, kind, pest, disease)
            for agent, kind, pest, disease in self.agent_repo.list_with_kind()
        ]

    def get_agent(self, agent_id: int) -> HarmfulAgentReadSchema | None:
        return self._load_agent_read(agent_id)

    def update_agent(
        self, agent_id: int, payload: HarmfulAgentUpdateSchema
    ) -> HarmfulAgentReadSchema | None:
        loaded = self.agent_repo.get_with_kind(agent_id)
        if loaded is None:
            return None
        _agent, kind, _pest, _disease = loaded
        data = payload.model_dump(exclude_unset=True)

        common = {
            key: data[key]
            for key in ("nome_comum", "nome_cientifico")
            if key in data
        }
        if common:
            self.agent_repo.update(agent_id, common)

        if kind == AgentKind.PEST:
            pest_data = {
                key: data[key]
                for key in ("tipo_praga", "habito_alimentar")
                if key in data
            }
            if pest_data:
                self.pest_repo.update(agent_id, pest_data)
        else:
            disease_data = {
                key: data[key]
                for key in ("agente_causador", "sintomas", "condicao_favoravel")
                if key in data
            }
            if disease_data:
                self.disease_repo.update(agent_id, disease_data)

        return self._load_agent_read(agent_id)

    def delete_agent(self, agent_id: int) -> bool:
        loaded = self.agent_repo.get_with_kind(agent_id)
        if loaded is None:
            return False
        _agent, kind, _pest, _disease = loaded

        occurrences = self.occurrence_repo.list(filters={"id_agente": agent_id})
        if occurrences:
            raise PhytosanitaryError(
                "Cannot delete agent linked to control occurrences"
            )

        if kind == AgentKind.PEST:
            self.pest_repo.delete(agent_id)
        else:
            self.disease_repo.delete(agent_id)
        return self.agent_repo.delete(agent_id)

    # --- Controls ---

    def create_control(self, payload: ControlCreateSchema) -> ControlReadSchema:
        """Create control header and optional occurrences in a single transaction."""
        header = payload.model_dump(exclude={"ocorrencias"})
        try:
            with get_session() as session:
                control = ControlModel(**header)
                session.add(control)
                session.flush()
                control_id = control.id_controle
                for occurrence in payload.ocorrencias:
                    session.add(
                        AgentOccurrenceModel(
                            id_controle=control_id, **occurrence.model_dump()
                        )
                    )
                session.flush()
        except IntegrityError as exc:
            raise PhytosanitaryError(
                "Could not create control. Check that id_plantio, "
                "id_funcionario and id_agente exist."
            ) from exc
        self._refresh_control_severity(control_id)
        loaded = self._load_control_read(control_id)
        assert loaded is not None
        return loaded

    def list_controls(self) -> list[ControlReadSchema]:
        return [
            self._to_control_read(control, produto_nome, funcionario_nome)
            for control, produto_nome, funcionario_nome in self.control_repo.list_with_labels()
        ]

    def get_control(self, control_id: int) -> ControlReadSchema | None:
        return self._load_control_read(control_id)

    def update_control(
        self, control_id: int, payload: ControlUpdateSchema
    ) -> ControlReadSchema | None:
        if self.control_repo.get_by_id(control_id) is None:
            return None
        data = payload.model_dump(exclude_unset=True)
        # Severity is derived from occurrence infestation levels.
        data.pop("nivel_severidade", None)
        try:
            record = self.control_repo.update(control_id, data)
        except IntegrityError as exc:
            raise PhytosanitaryError(
                "Could not update control. Check that id_plantio and "
                "id_funcionario exist."
            ) from exc
        if record is None:
            return None
        self._refresh_control_severity(control_id)
        return self._load_control_read(control_id)

    def delete_control(self, control_id: int) -> bool:
        if self.control_repo.get_by_id(control_id) is None:
            return False
        for application in self.application_repo.list(
            filters={"id_controle": control_id}
        ):
            self._reverse_application_stock(application)
            self.application_repo.delete(application.id_aplicacao)
        for occurrence in self.occurrence_repo.list(
            filters={"id_controle": control_id}
        ):
            self.occurrence_repo.delete(occurrence.id_ocorrencia)
        return self.control_repo.delete(control_id)

    # --- Occurrences (nested under control) ---

    def add_occurrence(
        self, control_id: int, payload: AgentOccurrenceCreateSchema
    ) -> AgentOccurrenceReadSchema | None:
        if self.control_repo.get_by_id(control_id) is None:
            return None
        if self.agent_repo.get_by_id(payload.id_agente) is None:
            raise PhytosanitaryError("Harmful agent not found")
        data = payload.model_dump()
        data["id_controle"] = control_id
        try:
            record = self.occurrence_repo.create(data)
        except IntegrityError as exc:
            raise PhytosanitaryError(
                "Could not add occurrence. Check that id_agente exists."
            ) from exc
        self._refresh_control_severity(control_id)
        return self._load_occurrence_read(record.id_ocorrencia)

    def list_occurrences(
        self, control_id: int
    ) -> list[AgentOccurrenceReadSchema] | None:
        if self.control_repo.get_by_id(control_id) is None:
            return None
        return [
            self._to_occurrence_read(occurrence, nome)
            for occurrence, nome in self.occurrence_repo.list_with_agent_name(
                control_id
            )
        ]

    def update_occurrence(
        self,
        control_id: int,
        occurrence_id: int,
        payload: AgentOccurrenceUpdateSchema,
    ) -> AgentOccurrenceReadSchema | None:
        if self.control_repo.get_by_id(control_id) is None:
            return None
        occurrence = self.occurrence_repo.get_by_id(occurrence_id)
        if occurrence is None or occurrence.id_controle != control_id:
            return None
        data = payload.model_dump(exclude_unset=True)
        if "id_agente" in data and self.agent_repo.get_by_id(data["id_agente"]) is None:
            raise PhytosanitaryError("Harmful agent not found")
        try:
            record = self.occurrence_repo.update(occurrence_id, data)
        except IntegrityError as exc:
            raise PhytosanitaryError(
                "Could not update occurrence. Check that id_agente exists."
            ) from exc
        if record is None:
            return None
        self._refresh_control_severity(control_id)
        return self._load_occurrence_read(occurrence_id)

    def delete_occurrence(self, control_id: int, occurrence_id: int) -> bool:
        if self.control_repo.get_by_id(control_id) is None:
            return False
        occurrence = self.occurrence_repo.get_by_id(occurrence_id)
        if occurrence is None or occurrence.id_controle != control_id:
            return False
        ok = self.occurrence_repo.delete(occurrence_id)
        if ok:
            self._refresh_control_severity(control_id)
        return ok

    # --- Pesticide applications (nested under control) ---

    def add_application(
        self, control_id: int, payload: PesticideApplicationCreateSchema
    ) -> PesticideApplicationReadSchema | None:
        if self.control_repo.get_by_id(control_id) is None:
            return None
        self._assert_pesticide_input(payload.id_insumo)
        self._assert_machine(payload.id_maquina)
        self._assert_withdrawal_dates(
            payload.dt_aplicacao,
            payload.dt_carencia,
            id_insumo=payload.id_insumo,
        )
        data = payload.model_dump()
        data["id_controle"] = control_id
        data["dt_carencia"] = self._resolve_withdrawal_date(
            payload.id_insumo, payload.dt_aplicacao, payload.dt_carencia
        )
        self._assert_withdrawal_dates(data["dt_aplicacao"], data["dt_carencia"])

        stock_meta: dict | None = None
        if payload.volume_aplicado is not None and payload.volume_aplicado > 0:
            stock_meta = self._debit_input_stock(
                id_insumo=payload.id_insumo,
                quantidade=payload.volume_aplicado,
            )
            data["id_estoque_saida"] = stock_meta["id_estoque"]
            data["id_lote_saida"] = stock_meta.get("id_lote")

        try:
            record = self.application_repo.create(data)
        except IntegrityError as exc:
            if stock_meta is not None:
                self._restore_input_stock(
                    id_insumo=payload.id_insumo,
                    quantidade=payload.volume_aplicado,
                    id_estoque=stock_meta["id_estoque"],
                    id_lote=stock_meta.get("id_lote"),
                )
            raise PhytosanitaryError(
                "Could not add application. Check that id_insumo exists."
            ) from exc

        self._notify_financial_cost(
            application_id=record.id_aplicacao,
            id_insumo=payload.id_insumo,
            volume=payload.volume_aplicado,
            dt_aplicacao=payload.dt_aplicacao,
        )
        return self._load_application_read(record.id_aplicacao)

    def _debit_input_stock(
        self, *, id_insumo: int, quantidade: float
    ) -> dict:
        """Debit stock for a pesticide application; raises if insufficient balance."""
        from decimal import Decimal

        from sqlalchemy import text

        from app.estoque.errors import EstoqueError
        from app.estoque.service import EstoqueService

        qty = Decimal(str(quantidade))
        with get_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT sl.id_estoque, sl.id_lote
                    FROM saldo_lote sl
                    JOIN lote l ON l.id_lote = sl.id_lote
                    WHERE l.id_produto = :produto
                      AND (sl.quantidade_atual - sl.quantidade_reservada) >= :qtd
                    ORDER BY sl.quantidade_atual DESC
                    LIMIT 1
                    """
                ),
                {"produto": id_insumo, "qtd": quantidade},
            ).first()
            if row is not None:
                id_estoque, id_lote = int(row[0]), int(row[1])
                try:
                    EstoqueService()._registrar_saida_simples(
                        id_estoque=id_estoque,
                        id_produto=id_insumo,
                        id_lote=id_lote,
                        quantidade=qty,
                        tipo="saida_atividade",
                    )
                except EstoqueError as exc:
                    raise PhytosanitaryError(exc.message) from exc
                return {"id_estoque": id_estoque, "id_lote": id_lote}

            row2 = session.execute(
                text(
                    """
                    SELECT id_estoque FROM saldo_estoque
                    WHERE id_produto = :produto AND quantidade_atual >= :qtd
                    ORDER BY quantidade_atual DESC
                    LIMIT 1
                    """
                ),
                {"produto": id_insumo, "qtd": quantidade},
            ).first()
            if row2 is None:
                raise PhytosanitaryError(
                    "Insufficient stock for pesticide application"
                )
            id_estoque = int(row2[0])
            try:
                EstoqueService()._registrar_saida_simples(
                    id_estoque=id_estoque,
                    id_produto=id_insumo,
                    id_lote=None,
                    quantidade=qty,
                    tipo="saida_atividade",
                )
            except EstoqueError as exc:
                raise PhytosanitaryError(exc.message) from exc
            return {"id_estoque": id_estoque, "id_lote": None}

    def _restore_input_stock(
        self,
        *,
        id_insumo: int,
        quantidade: float | None,
        id_estoque: int | None,
        id_lote: int | None,
    ) -> None:
        if (
            quantidade is None
            or quantidade <= 0
            or id_estoque is None
        ):
            return
        from decimal import Decimal

        from app.estoque.errors import EstoqueError
        from app.estoque.service import EstoqueService

        try:
            EstoqueService().registrar_estorno_saida(
                id_estoque=id_estoque,
                id_produto=id_insumo,
                id_lote=id_lote,
                quantidade=Decimal(str(quantidade)),
            )
        except EstoqueError as exc:
            raise PhytosanitaryError(exc.message) from exc

    def _reverse_application_stock(self, application) -> None:
        self._restore_input_stock(
            id_insumo=application.id_insumo,
            quantidade=(
                float(application.volume_aplicado)
                if application.volume_aplicado is not None
                else None
            ),
            id_estoque=getattr(application, "id_estoque_saida", None),
            id_lote=getattr(application, "id_lote_saida", None),
        )

    def _notify_financial_cost(
        self,
        *,
        application_id: int,
        id_insumo: int,
        volume: float | None,
        dt_aplicacao,
    ) -> None:
        if volume is None or volume <= 0:
            return
        preco = self.lookup_repo.get_product_price(id_insumo)
        if preco is None:
            return
        from decimal import Decimal

        from app.financeiro.service import FinanceiroService

        valor = Decimal(str(preco)) * Decimal(str(volume))
        try:
            FinanceiroService().register_phytosanitary_cost(
                id_aplicacao=application_id,
                valor=valor,
                data_movimento=dt_aplicacao,
            )
        except Exception:
            return

    def list_applications(
        self, control_id: int
    ) -> list[PesticideApplicationReadSchema] | None:
        if self.control_repo.get_by_id(control_id) is None:
            return None
        return [
            self._to_application_read(application, nome, maquina_nome)
            for application, nome, maquina_nome in self.application_repo.list_with_input_name(
                control_id
            )
        ]

    def update_application(
        self,
        control_id: int,
        application_id: int,
        payload: PesticideApplicationUpdateSchema,
    ) -> PesticideApplicationReadSchema | None:
        if self.control_repo.get_by_id(control_id) is None:
            return None
        application = self.application_repo.get_by_id(application_id)
        if application is None or application.id_controle != control_id:
            return None

        data = payload.model_dump(exclude_unset=True)
        id_insumo = data.get("id_insumo", application.id_insumo)
        dt_aplicacao = data.get("dt_aplicacao", application.dt_aplicacao)
        dt_carencia = data.get("dt_carencia", application.dt_carencia)
        id_maquina = data.get("id_maquina", application.id_maquina)
        volume = data.get("volume_aplicado", application.volume_aplicado)

        self._assert_pesticide_input(id_insumo)
        self._assert_machine(id_maquina)

        if "id_insumo" in data or "dt_aplicacao" in data:
            if "dt_carencia" not in data:
                computed = self._resolve_withdrawal_date(
                    id_insumo, dt_aplicacao, None
                )
                if computed is not None:
                    data["dt_carencia"] = computed
                    dt_carencia = computed

        self._assert_withdrawal_dates(
            dt_aplicacao, data.get("dt_carencia", dt_carencia), id_insumo=id_insumo
        )

        stock_changed = (
            "id_insumo" in data
            or "volume_aplicado" in data
        )
        if stock_changed:
            self._reverse_application_stock(application)
            data["id_estoque_saida"] = None
            data["id_lote_saida"] = None
            if volume is not None and float(volume) > 0:
                stock_meta = self._debit_input_stock(
                    id_insumo=id_insumo,
                    quantidade=float(volume),
                )
                data["id_estoque_saida"] = stock_meta["id_estoque"]
                data["id_lote_saida"] = stock_meta.get("id_lote")

        try:
            record = self.application_repo.update(application_id, data)
        except IntegrityError as exc:
            raise PhytosanitaryError(
                "Could not update application. Check that id_insumo exists."
            ) from exc
        if record is None:
            return None

        if stock_changed and volume is not None and float(volume) > 0:
            old_vol = (
                float(application.volume_aplicado)
                if application.volume_aplicado is not None
                else 0.0
            )
            new_vol = float(volume)
            if new_vol > old_vol or id_insumo != application.id_insumo:
                self._notify_financial_cost(
                    application_id=application_id,
                    id_insumo=id_insumo,
                    volume=new_vol if id_insumo != application.id_insumo else (new_vol - old_vol),
                    dt_aplicacao=dt_aplicacao,
                )

        return self._load_application_read(application_id)

    def delete_application(self, control_id: int, application_id: int) -> bool:
        if self.control_repo.get_by_id(control_id) is None:
            return False
        application = self.application_repo.get_by_id(application_id)
        if application is None or application.id_controle != control_id:
            return False
        self._reverse_application_stock(application)
        return self.application_repo.delete(application_id)
