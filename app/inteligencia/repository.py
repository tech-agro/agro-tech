"""Acesso a dados do dominio inteligencia."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.core.base_repository import BaseRepository
from app.core.database import get_session
from app.financeiro.models import ContaPagarModel
from app.fitossanidade.enum import SEVERITY_RANK
from app.fitossanidade.models.agent_occurrence import AgentOccurrenceModel
from app.fitossanidade.models.control import ControlModel
from app.fitossanidade.models.harmful_agent import HarmfulAgentModel
from app.fitossanidade.models.pesticide_application import PesticideApplicationModel
from app.inteligencia.models import IndicadorModel, MedicaoIndicadorModel
from app.inteligencia.refs import (
    ColheitaRef,
    CulturaRef,
    PlanejamentoSafraRef,
    PlantioRef,
    SafraRef,
    TalhaoRef,
)
from app.inteligencia.schemas import (
    CustoFitossanidadeTalhaoSchema,
    IndicadorAgregacaoSchema,
    IndicadorCreateSchema,
    IndicadorReadSchema,
    IndicadorUpdateSchema,
    MedicaoIndicadorCreateSchema,
    MedicaoIndicadorReadSchema,
    MedicaoIndicadorUpdateSchema,
    OcorrenciaFitossanidadeSchema,
    ProdutividadeTalhaoSchema,
)


@dataclass(frozen=True, slots=True)
class IndicadorFilters:
    """Filtros opcionais para listagem de indicadores."""

    nome: str | None = None
    unidade: str | None = None


class IndicadorRepository(BaseRepository[IndicadorModel]):
    """CRUD e consultas da entidade indicador."""

    model = IndicadorModel

    def create_indicador(self, payload: IndicadorCreateSchema) -> IndicadorReadSchema:
        registro = self.create(payload.model_dump())
        return IndicadorReadSchema.model_validate(registro)

    def get_indicador(self, id_indicador: int) -> IndicadorReadSchema | None:
        registro = self.get_by_id(id_indicador)
        if registro is None:
            return None
        return IndicadorReadSchema.model_validate(registro)

    def list_indicadores(
        self,
        filters: IndicadorFilters | None = None,
    ) -> list[IndicadorReadSchema]:
        with get_session() as session:
            query = select(IndicadorModel).order_by(IndicadorModel.nome)
            if filters is not None:
                if filters.nome:
                    query = query.where(IndicadorModel.nome.ilike(f"%{filters.nome}%"))
                if filters.unidade:
                    query = query.where(IndicadorModel.unidade == filters.unidade)
            registros = session.scalars(query).all()
            result: list[IndicadorReadSchema] = []
            for registro in registros:
                session.expunge(registro)
                result.append(IndicadorReadSchema.model_validate(registro))
            return result

    def update_indicador(
        self,
        id_indicador: int,
        payload: IndicadorUpdateSchema,
    ) -> IndicadorReadSchema | None:
        dados = payload.model_dump(exclude_unset=True)
        if not dados:
            return self.get_indicador(id_indicador)
        registro = self.update(id_indicador, dados)
        if registro is None:
            return None
        return IndicadorReadSchema.model_validate(registro)

    def delete_indicador(self, id_indicador: int) -> bool:
        return self.delete(id_indicador)

    def exists(self, id_indicador: int) -> bool:
        with get_session() as session:
            return (
                session.scalar(
                    select(IndicadorModel.id_indicador)
                    .where(IndicadorModel.id_indicador == id_indicador)
                    .limit(1)
                )
                is not None
            )

    def get_by_nome(self, nome: str) -> IndicadorReadSchema | None:
        with get_session() as session:
            registro = session.scalars(
                select(IndicadorModel).where(
                    func.lower(IndicadorModel.nome) == nome.strip().lower()
                )
            ).first()
            if registro is None:
                return None
            session.expunge(registro)
            return IndicadorReadSchema.model_validate(registro)

    def count_medicoes(self, id_indicador: int) -> int:
        with get_session() as session:
            total = session.scalar(
                select(func.count())
                .select_from(MedicaoIndicadorModel)
                .where(MedicaoIndicadorModel.id_indicador == id_indicador)
            )
            return int(total or 0)


@dataclass(frozen=True, slots=True)
class MedicaoIndicadorFilters:
    """Filtros opcionais para listagem de medicoes."""

    id_indicador: int | None = None
    id_safra: int | None = None
    data_inicio: date | None = None
    data_fim: date | None = None


class MedicaoIndicadorRepository(BaseRepository[MedicaoIndicadorModel]):
    """CRUD e consultas da entidade medicao_indicador."""

    model = MedicaoIndicadorModel

    def exists_safra(self, id_safra: int) -> bool:
        with get_session() as session:
            return (
                session.scalar(
                    select(SafraRef.id_safra).where(SafraRef.id_safra == id_safra).limit(1)
                )
                is not None
            )

    def get_safra_nome(self, id_safra: int) -> str | None:
        with get_session() as session:
            return session.scalar(
                select(SafraRef.nome).where(SafraRef.id_safra == id_safra)
            )

    def create_medicao(
        self,
        payload: MedicaoIndicadorCreateSchema,
    ) -> MedicaoIndicadorReadSchema:
        registro = self.create(payload.model_dump())
        return self._to_read(registro)

    def get_medicao(self, id_medicao: int) -> MedicaoIndicadorReadSchema | None:
        loaded = self.get_with_labels(id_medicao)
        return loaded

    def list_medicoes(
        self,
        filters: MedicaoIndicadorFilters | None = None,
    ) -> list[MedicaoIndicadorReadSchema]:
        with get_session() as session:
            query = (
                select(
                    MedicaoIndicadorModel,
                    IndicadorModel.nome,
                    SafraRef.nome,
                )
                .join(IndicadorModel, IndicadorModel.id_indicador == MedicaoIndicadorModel.id_indicador)
                .outerjoin(SafraRef, SafraRef.id_safra == MedicaoIndicadorModel.id_safra)
                .order_by(
                    MedicaoIndicadorModel.data_referencia.desc(),
                    MedicaoIndicadorModel.id_medicao.desc(),
                )
            )
            if filters is not None:
                if filters.id_indicador is not None:
                    query = query.where(
                        MedicaoIndicadorModel.id_indicador == filters.id_indicador
                    )
                if filters.id_safra is not None:
                    query = query.where(MedicaoIndicadorModel.id_safra == filters.id_safra)
                if filters.data_inicio is not None:
                    query = query.where(
                        MedicaoIndicadorModel.data_referencia >= filters.data_inicio
                    )
                if filters.data_fim is not None:
                    query = query.where(
                        MedicaoIndicadorModel.data_referencia <= filters.data_fim
                    )
            rows = session.execute(query).all()
            result: list[MedicaoIndicadorReadSchema] = []
            for medicao, indicador_nome, safra_nome in rows:
                session.expunge(medicao)
                result.append(
                    self._to_read(medicao, indicador_nome=indicador_nome, safra_nome=safra_nome)
                )
            return result

    def update_medicao(
        self,
        id_medicao: int,
        payload: MedicaoIndicadorUpdateSchema,
    ) -> MedicaoIndicadorReadSchema | None:
        dados = payload.model_dump(exclude_unset=True)
        if not dados:
            return self.get_medicao(id_medicao)
        registro = self.update(id_medicao, dados)
        if registro is None:
            return None
        return self.get_with_labels(id_medicao)

    def delete_medicao(self, id_medicao: int) -> bool:
        return self.delete(id_medicao)

    def exists_medicao_duplicada(
        self,
        *,
        id_indicador: int,
        id_safra: int,
        data_referencia: date,
        exclude_id: int | None = None,
    ) -> bool:
        with get_session() as session:
            query = select(MedicaoIndicadorModel.id_medicao).where(
                MedicaoIndicadorModel.id_indicador == id_indicador,
                MedicaoIndicadorModel.id_safra == id_safra,
                MedicaoIndicadorModel.data_referencia == data_referencia,
            )
            if exclude_id is not None:
                query = query.where(MedicaoIndicadorModel.id_medicao != exclude_id)
            return session.scalar(query.limit(1)) is not None

    def agregar_medicoes(
        self,
        *,
        id_indicador: int,
        id_safra: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> IndicadorAgregacaoSchema:
        with get_session() as session:
            query = select(
                func.count(MedicaoIndicadorModel.id_medicao),
                func.avg(MedicaoIndicadorModel.valor),
                func.min(MedicaoIndicadorModel.valor),
                func.max(MedicaoIndicadorModel.valor),
                func.sum(MedicaoIndicadorModel.valor),
            ).where(
                MedicaoIndicadorModel.id_indicador == id_indicador,
                MedicaoIndicadorModel.valor.isnot(None),
            )
            if id_safra is not None:
                query = query.where(MedicaoIndicadorModel.id_safra == id_safra)
            if data_inicio is not None:
                query = query.where(MedicaoIndicadorModel.data_referencia >= data_inicio)
            if data_fim is not None:
                query = query.where(MedicaoIndicadorModel.data_referencia <= data_fim)

            total, media, minimo, maximo, soma = session.execute(query).one()

            indicador_nome = session.scalar(
                select(IndicadorModel.nome).where(
                    IndicadorModel.id_indicador == id_indicador
                )
            )
            safra_nome = (
                session.scalar(select(SafraRef.nome).where(SafraRef.id_safra == id_safra))
                if id_safra is not None
                else None
            )

            return IndicadorAgregacaoSchema(
                id_indicador=id_indicador,
                indicador_nome=indicador_nome,
                id_safra=id_safra,
                safra_nome=safra_nome,
                data_inicio=data_inicio,
                data_fim=data_fim,
                total_medicoes=int(total or 0),
                valor_medio=_to_decimal(media),
                valor_minimo=_to_decimal(minimo),
                valor_maximo=_to_decimal(maximo),
                valor_soma=_to_decimal(soma),
            )

    def get_with_labels(self, id_medicao: int) -> MedicaoIndicadorReadSchema | None:
        with get_session() as session:
            row = session.execute(
                select(MedicaoIndicadorModel, IndicadorModel.nome, SafraRef.nome)
                .join(
                    IndicadorModel,
                    IndicadorModel.id_indicador == MedicaoIndicadorModel.id_indicador,
                )
                .outerjoin(SafraRef, SafraRef.id_safra == MedicaoIndicadorModel.id_safra)
                .where(MedicaoIndicadorModel.id_medicao == id_medicao)
            ).first()
            if row is None:
                return None
            medicao, indicador_nome, safra_nome = row
            session.expunge(medicao)
            return self._to_read(medicao, indicador_nome=indicador_nome, safra_nome=safra_nome)

    @staticmethod
    def _to_read(
        medicao: MedicaoIndicadorModel,
        *,
        indicador_nome: str | None = None,
        safra_nome: str | None = None,
    ) -> MedicaoIndicadorReadSchema:
        data = MedicaoIndicadorReadSchema.model_validate(medicao).model_dump()
        data["indicador_nome"] = indicador_nome
        data["safra_nome"] = safra_nome
        return MedicaoIndicadorReadSchema.model_validate(data)


def _to_decimal(valor: object | None) -> Decimal | None:
    if valor is None:
        return None
    return Decimal(str(valor))


class ProdutividadeRepository:
    """Produtividade (kg/ha) planejada x realizada por talhao/safra."""

    def listar(
        self,
        *,
        id_safra: int | None = None,
        id_talhao: int | None = None,
    ) -> list[ProdutividadeTalhaoSchema]:
        with get_session() as session:
            colhido = (
                select(
                    PlantioRef.id_talhao.label("id_talhao"),
                    func.sum(ColheitaRef.quantidade_colhida).label("total_colhido"),
                )
                .join(ColheitaRef, ColheitaRef.id_plantio == PlantioRef.id_plantio)
                .group_by(PlantioRef.id_talhao)
                .subquery()
            )
            query = (
                select(
                    TalhaoRef.id_talhao,
                    TalhaoRef.nome,
                    SafraRef.id_safra,
                    SafraRef.nome,
                    SafraRef.ano,
                    CulturaRef.nome,
                    TalhaoRef.area_hectares,
                    PlanejamentoSafraRef.meta_produtividade,
                    PlanejamentoSafraRef.area_planejada,
                    colhido.c.total_colhido,
                )
                .select_from(TalhaoRef)
                .join(SafraRef, SafraRef.id_safra == TalhaoRef.id_safra)
                .outerjoin(
                    PlanejamentoSafraRef,
                    (PlanejamentoSafraRef.id_talhao == TalhaoRef.id_talhao)
                    & (PlanejamentoSafraRef.id_safra == TalhaoRef.id_safra),
                )
                .outerjoin(CulturaRef, CulturaRef.id_cultura == PlanejamentoSafraRef.id_cultura)
                .outerjoin(colhido, colhido.c.id_talhao == TalhaoRef.id_talhao)
                .order_by(SafraRef.ano, SafraRef.nome, TalhaoRef.nome)
            )
            if id_safra is not None:
                query = query.where(TalhaoRef.id_safra == id_safra)
            if id_talhao is not None:
                query = query.where(TalhaoRef.id_talhao == id_talhao)

            rows = session.execute(query).all()
            resultado: list[ProdutividadeTalhaoSchema] = []
            for (
                id_talhao_row,
                talhao_nome,
                id_safra_row,
                safra_nome,
                safra_ano,
                cultura_nome,
                area_hectares,
                meta_produtividade,
                area_planejada,
                total_colhido,
            ) in rows:
                area_referencia = area_planejada or area_hectares
                realizado = None
                if total_colhido is not None and area_referencia:
                    realizado = (Decimal(str(total_colhido)) / Decimal(str(area_referencia))).quantize(
                        Decimal("0.01")
                    )
                variacao = None
                if realizado is not None and meta_produtividade:
                    meta_decimal = Decimal(str(meta_produtividade))
                    variacao = (
                        (realizado - meta_decimal) / meta_decimal * 100
                    ).quantize(Decimal("0.01"))
                resultado.append(
                    ProdutividadeTalhaoSchema(
                        id_talhao=id_talhao_row,
                        talhao_nome=talhao_nome,
                        id_safra=id_safra_row,
                        safra_nome=safra_nome,
                        safra_ano=safra_ano,
                        cultura_nome=cultura_nome,
                        area_hectares=_to_decimal(area_hectares),
                        meta_produtividade=_to_decimal(meta_produtividade),
                        quantidade_colhida_total=_to_decimal(total_colhido),
                        produtividade_realizada=realizado,
                        variacao_percentual=variacao,
                    )
                )
            return resultado


class FitossanidadeBiRepository:
    """Custo de defensivos e ocorrencias por talhao/safra (leitura para BI)."""

    def custos_por_talhao(
        self,
        *,
        id_safra: int | None = None,
        id_talhao: int | None = None,
    ) -> list[CustoFitossanidadeTalhaoSchema]:
        with get_session() as session:
            query = (
                select(
                    TalhaoRef.id_talhao,
                    TalhaoRef.nome,
                    SafraRef.id_safra,
                    SafraRef.nome,
                    SafraRef.ano,
                    func.count(func.distinct(PesticideApplicationModel.id_aplicacao)),
                    func.coalesce(func.sum(ContaPagarModel.valor), 0),
                )
                .select_from(TalhaoRef)
                .join(SafraRef, SafraRef.id_safra == TalhaoRef.id_safra)
                .outerjoin(PlantioRef, PlantioRef.id_talhao == TalhaoRef.id_talhao)
                .outerjoin(ControlModel, ControlModel.id_plantio == PlantioRef.id_plantio)
                .outerjoin(
                    PesticideApplicationModel,
                    PesticideApplicationModel.id_controle == ControlModel.id_controle,
                )
                .outerjoin(
                    ContaPagarModel,
                    ContaPagarModel.id_aplicacao == PesticideApplicationModel.id_aplicacao,
                )
                .group_by(
                    TalhaoRef.id_talhao, TalhaoRef.nome, SafraRef.id_safra, SafraRef.nome, SafraRef.ano
                )
                .order_by(SafraRef.ano, SafraRef.nome, TalhaoRef.nome)
            )
            if id_safra is not None:
                query = query.where(TalhaoRef.id_safra == id_safra)
            if id_talhao is not None:
                query = query.where(TalhaoRef.id_talhao == id_talhao)

            rows = session.execute(query).all()
            return [
                CustoFitossanidadeTalhaoSchema(
                    id_talhao=id_talhao_row,
                    talhao_nome=talhao_nome,
                    id_safra=id_safra_row,
                    safra_nome=safra_nome,
                    safra_ano=safra_ano,
                    total_aplicacoes=int(total_aplicacoes or 0),
                    custo_total=_to_decimal(custo_total) or Decimal("0"),
                )
                for (
                    id_talhao_row,
                    talhao_nome,
                    id_safra_row,
                    safra_nome,
                    safra_ano,
                    total_aplicacoes,
                    custo_total,
                ) in rows
            ]

    def ocorrencias_por_severidade(
        self,
        *,
        id_safra: int | None = None,
        id_talhao: int | None = None,
    ) -> list[OcorrenciaFitossanidadeSchema]:
        with get_session() as session:
            query = (
                select(
                    SafraRef.id_safra,
                    SafraRef.nome,
                    SafraRef.ano,
                    TalhaoRef.id_talhao,
                    TalhaoRef.nome,
                    ControlModel.nivel_severidade,
                    HarmfulAgentModel.nome_comum,
                    func.count(AgentOccurrenceModel.id_ocorrencia),
                )
                .select_from(AgentOccurrenceModel)
                .join(ControlModel, ControlModel.id_controle == AgentOccurrenceModel.id_controle)
                .join(HarmfulAgentModel, HarmfulAgentModel.id_agente == AgentOccurrenceModel.id_agente)
                .join(PlantioRef, PlantioRef.id_plantio == ControlModel.id_plantio)
                .join(TalhaoRef, TalhaoRef.id_talhao == PlantioRef.id_talhao)
                .join(SafraRef, SafraRef.id_safra == TalhaoRef.id_safra)
                .group_by(
                    SafraRef.id_safra,
                    SafraRef.nome,
                    SafraRef.ano,
                    TalhaoRef.id_talhao,
                    TalhaoRef.nome,
                    ControlModel.nivel_severidade,
                    HarmfulAgentModel.nome_comum,
                )
            )
            if id_safra is not None:
                query = query.where(TalhaoRef.id_safra == id_safra)
            if id_talhao is not None:
                query = query.where(TalhaoRef.id_talhao == id_talhao)

            rows = session.execute(query).all()
            resultado = [
                OcorrenciaFitossanidadeSchema(
                    id_safra=id_safra_row,
                    safra_nome=safra_nome,
                    safra_ano=safra_ano,
                    id_talhao=id_talhao_row,
                    talhao_nome=talhao_nome,
                    nivel_severidade=nivel_severidade,
                    agente_nome=agente_nome,
                    total_ocorrencias=int(total or 0),
                )
                for (
                    id_safra_row,
                    safra_nome,
                    safra_ano,
                    id_talhao_row,
                    talhao_nome,
                    nivel_severidade,
                    agente_nome,
                    total,
                ) in rows
            ]
            resultado.sort(
                key=lambda item: (
                    item.safra_nome,
                    item.talhao_nome,
                    -SEVERITY_RANK.get(item.nivel_severidade or "", 0),
                )
            )
            return resultado


class InteligenciaRepository(IndicadorRepository):
    """Facade do repositorio de inteligencia (compativel com service/controller)."""

    pass