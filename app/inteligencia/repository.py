"""Acesso a dados do dominio inteligencia."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select

from app.core.base_repository import BaseRepository
from app.core.database import get_session
from app.inteligencia.models import IndicadorModel, MedicaoIndicadorModel
from app.inteligencia.schemas import (
    IndicadorCreateSchema,
    IndicadorReadSchema,
    IndicadorUpdateSchema,
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


class InteligenciaRepository(IndicadorRepository):
    """Facade do repositorio de inteligencia (compativel com service/controller)."""

    pass
