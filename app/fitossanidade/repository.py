"""Data access for the phytosanitary domain."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from app.core.base_repository import BaseRepository
from app.core.database import get_session

from app.fitossanidade.enum import DEFENSIVE_CATEGORY_NAME, PESTICIDE_CLASSES, AgentKind
from app.fitossanidade.models.agent_occurrence import AgentOccurrenceModel
from app.fitossanidade.models.control import ControlModel
from app.fitossanidade.models.disease import DiseaseModel
from app.fitossanidade.models.harmful_agent import HarmfulAgentModel
from app.fitossanidade.models.pest import PestModel
from app.fitossanidade.models.pesticide_application import PesticideApplicationModel
from app.fitossanidade.models.refs import (
    FuncionarioRef,
    InsumoRef,
    MaquinaRef,
    PessoaRef,
    PlantioRef,
    ProdutoRef,
)

# Register FK targets on SQLAlchemy metadata (shared tables owned elsewhere).
_ = (
    PessoaRef,
    FuncionarioRef,
    PlantioRef,
    ProdutoRef,
    InsumoRef,
    MaquinaRef,
)


class HarmfulAgentRepository(BaseRepository[HarmfulAgentModel]):
    model = HarmfulAgentModel

    def list_with_kind(self) -> list[tuple[HarmfulAgentModel, AgentKind, PestModel | None, DiseaseModel | None]]:
        with get_session() as session:
            rows = session.execute(
                select(HarmfulAgentModel, PestModel, DiseaseModel)
                .outerjoin(PestModel, PestModel.id_agente == HarmfulAgentModel.id_agente)
                .outerjoin(
                    DiseaseModel, DiseaseModel.id_agente == HarmfulAgentModel.id_agente
                )
                .order_by(HarmfulAgentModel.id_agente)
            ).all()
            result: list[
                tuple[HarmfulAgentModel, AgentKind, PestModel | None, DiseaseModel | None]
            ] = []
            for agent, pest, disease in rows:
                session.expunge(agent)
                if pest is not None:
                    session.expunge(pest)
                    result.append((agent, AgentKind.PEST, pest, None))
                elif disease is not None:
                    session.expunge(disease)
                    result.append((agent, AgentKind.DISEASE, None, disease))
            return result

    def get_with_kind(
        self, agent_id: int
    ) -> tuple[HarmfulAgentModel, AgentKind, PestModel | None, DiseaseModel | None] | None:
        with get_session() as session:
            row = session.execute(
                select(HarmfulAgentModel, PestModel, DiseaseModel)
                .outerjoin(PestModel, PestModel.id_agente == HarmfulAgentModel.id_agente)
                .outerjoin(
                    DiseaseModel, DiseaseModel.id_agente == HarmfulAgentModel.id_agente
                )
                .where(HarmfulAgentModel.id_agente == agent_id)
            ).first()
            if row is None:
                return None
            agent, pest, disease = row
            session.expunge(agent)
            if pest is not None:
                session.expunge(pest)
                return agent, AgentKind.PEST, pest, None
            if disease is not None:
                session.expunge(disease)
                return agent, AgentKind.DISEASE, None, disease
            return None


class PestRepository(BaseRepository[PestModel]):
    model = PestModel


class DiseaseRepository(BaseRepository[DiseaseModel]):
    model = DiseaseModel


class ControlRepository(BaseRepository[ControlModel]):
    model = ControlModel

    def list_with_labels(
        self,
    ) -> list[tuple[ControlModel, str | None, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(ControlModel, ProdutoRef.nome, PessoaRef.nome)
                .outerjoin(PlantioRef, PlantioRef.id_plantio == ControlModel.id_plantio)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == PlantioRef.id_produto)
                .outerjoin(
                    FuncionarioRef,
                    FuncionarioRef.id_funcionario == ControlModel.id_funcionario,
                )
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == FuncionarioRef.id_pessoa)
                .order_by(ControlModel.id_controle)
            ).all()
            result: list[tuple[ControlModel, str | None, str | None]] = []
            for control, produto_nome, funcionario_nome in rows:
                session.expunge(control)
                result.append((control, produto_nome, funcionario_nome))
            return result

    def get_with_labels(
        self, control_id: int
    ) -> tuple[ControlModel, str | None, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(ControlModel, ProdutoRef.nome, PessoaRef.nome)
                .outerjoin(PlantioRef, PlantioRef.id_plantio == ControlModel.id_plantio)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == PlantioRef.id_produto)
                .outerjoin(
                    FuncionarioRef,
                    FuncionarioRef.id_funcionario == ControlModel.id_funcionario,
                )
                .outerjoin(PessoaRef, PessoaRef.id_pessoa == FuncionarioRef.id_pessoa)
                .where(ControlModel.id_controle == control_id)
            ).first()
            if row is None:
                return None
            control, produto_nome, funcionario_nome = row
            session.expunge(control)
            return control, produto_nome, funcionario_nome


class AgentOccurrenceRepository(BaseRepository[AgentOccurrenceModel]):
    model = AgentOccurrenceModel

    def list_with_agent_name(
        self, control_id: int
    ) -> list[tuple[AgentOccurrenceModel, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(AgentOccurrenceModel, HarmfulAgentModel.nome_comum)
                .outerjoin(
                    HarmfulAgentModel,
                    HarmfulAgentModel.id_agente == AgentOccurrenceModel.id_agente,
                )
                .where(AgentOccurrenceModel.id_controle == control_id)
                .order_by(AgentOccurrenceModel.id_ocorrencia)
            ).all()
            result: list[tuple[AgentOccurrenceModel, str | None]] = []
            for occurrence, nome in rows:
                session.expunge(occurrence)
                result.append((occurrence, nome))
            return result

    def get_with_agent_name(
        self, occurrence_id: int
    ) -> tuple[AgentOccurrenceModel, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(AgentOccurrenceModel, HarmfulAgentModel.nome_comum)
                .outerjoin(
                    HarmfulAgentModel,
                    HarmfulAgentModel.id_agente == AgentOccurrenceModel.id_agente,
                )
                .where(AgentOccurrenceModel.id_ocorrencia == occurrence_id)
            ).first()
            if row is None:
                return None
            occurrence, nome = row
            session.expunge(occurrence)
            return occurrence, nome


class PesticideApplicationRepository(BaseRepository[PesticideApplicationModel]):
    model = PesticideApplicationModel

    def list_with_input_name(
        self, control_id: int
    ) -> list[tuple[PesticideApplicationModel, str | None, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(PesticideApplicationModel, ProdutoRef.nome, MaquinaRef.nome)
                .outerjoin(
                    InsumoRef, InsumoRef.id_produto == PesticideApplicationModel.id_insumo
                )
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == InsumoRef.id_produto)
                .outerjoin(
                    MaquinaRef,
                    MaquinaRef.id_maquina == PesticideApplicationModel.id_maquina,
                )
                .where(PesticideApplicationModel.id_controle == control_id)
                .order_by(PesticideApplicationModel.id_aplicacao)
            ).all()
            result: list[tuple[PesticideApplicationModel, str | None, str | None]] = []
            for application, nome, maquina_nome in rows:
                session.expunge(application)
                result.append((application, nome, maquina_nome))
            return result

    def get_with_input_name(
        self, application_id: int
    ) -> tuple[PesticideApplicationModel, str | None, str | None] | None:
        with get_session() as session:
            row = session.execute(
                select(PesticideApplicationModel, ProdutoRef.nome, MaquinaRef.nome)
                .outerjoin(
                    InsumoRef, InsumoRef.id_produto == PesticideApplicationModel.id_insumo
                )
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == InsumoRef.id_produto)
                .outerjoin(
                    MaquinaRef,
                    MaquinaRef.id_maquina == PesticideApplicationModel.id_maquina,
                )
                .where(PesticideApplicationModel.id_aplicacao == application_id)
            ).first()
            if row is None:
                return None
            application, nome, maquina_nome = row
            session.expunge(application)
            return application, nome, maquina_nome


class PhytosanitaryLookupRepository:
    """Read-only access to shared tables for phytosanitary UI labels."""

    def list_plantings(self) -> list[tuple[PlantioRef, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(PlantioRef, ProdutoRef.nome)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == PlantioRef.id_produto)
                .order_by(PlantioRef.id_plantio)
            ).all()
            result: list[tuple[PlantioRef, str | None]] = []
            for plantio, nome in rows:
                session.expunge(plantio)
                result.append((plantio, nome))
            return result

    def list_employees(self) -> list[tuple[FuncionarioRef, str]]:
        with get_session() as session:
            rows = session.execute(
                select(FuncionarioRef, PessoaRef.nome)
                .join(PessoaRef, PessoaRef.id_pessoa == FuncionarioRef.id_pessoa)
                .order_by(PessoaRef.nome)
            ).all()
            result: list[tuple[FuncionarioRef, str]] = []
            for funcionario, nome in rows:
                session.expunge(funcionario)
                result.append((funcionario, nome))
            return result

    def list_inputs(self) -> list[tuple[InsumoRef, str]]:
        """Return only pesticide inputs (defensivos)."""
        from sqlalchemy import text

        with get_session() as session:
            rows = session.execute(
                text(
                    """
                    SELECT i.id_produto, i.classe_agronomica, i.principio_ativo,
                           i.periodo_carencia_dias, i.registro_mapa, p.nome
                    FROM insumo i
                    JOIN produto p ON p.id_produto = i.id_produto
                    JOIN categoria_produto c ON c.id_categoria = p.id_categoria
                    WHERE c.nome = :categoria
                       OR i.classe_agronomica = ANY(:classes)
                    ORDER BY p.nome
                    """
                ),
                {
                    "categoria": DEFENSIVE_CATEGORY_NAME,
                    "classes": list(PESTICIDE_CLASSES),
                },
            ).all()
            result: list[tuple[InsumoRef, str]] = []
            for row in rows:
                insumo = InsumoRef(
                    id_produto=row[0],
                    classe_agronomica=row[1],
                    principio_ativo=row[2],
                    periodo_carencia_dias=row[3],
                    registro_mapa=row[4],
                )
                result.append((insumo, row[5]))
            return result

    def is_pesticide_input(self, id_insumo: int) -> bool:
        from sqlalchemy import text

        with get_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT 1
                    FROM insumo i
                    JOIN produto p ON p.id_produto = i.id_produto
                    JOIN categoria_produto c ON c.id_categoria = p.id_categoria
                    WHERE i.id_produto = :id
                      AND (c.nome = :categoria OR i.classe_agronomica = ANY(:classes))
                    LIMIT 1
                    """
                ),
                {
                    "id": id_insumo,
                    "categoria": DEFENSIVE_CATEGORY_NAME,
                    "classes": list(PESTICIDE_CLASSES),
                },
            ).first()
            return row is not None

    def get_product_price(self, id_produto: int):
        from sqlalchemy import text

        with get_session() as session:
            row = session.execute(
                text("SELECT preco FROM produto WHERE id_produto = :id"),
                {"id": id_produto},
            ).first()
            return row[0] if row is not None else None

    def list_machines(self) -> list[MaquinaRef]:
        with get_session() as session:
            rows = session.execute(
                select(MaquinaRef).order_by(MaquinaRef.nome, MaquinaRef.id_maquina)
            ).scalars().all()
            result: list[MaquinaRef] = []
            for machine in rows:
                session.expunge(machine)
                result.append(machine)
            return result

    def get_machine(self, id_maquina: int) -> MaquinaRef | None:
        with get_session() as session:
            row = session.get(MaquinaRef, id_maquina)
            if row is None:
                return None
            session.expunge(row)
            return row

    def get_input(self, id_insumo: int) -> InsumoRef | None:
        with get_session() as session:
            row = session.get(InsumoRef, id_insumo)
            if row is None:
                return None
            session.expunge(row)
            return row

    def compute_withdrawal_date(self, id_insumo: int, dt_aplicacao):
        """Return dt_aplicacao + periodo_carencia_dias when both are known."""
        if dt_aplicacao is None:
            return None
        insumo = self.get_input(id_insumo)
        if insumo is None or insumo.periodo_carencia_dias is None:
            return None
        return dt_aplicacao + timedelta(days=int(insumo.periodo_carencia_dias))
