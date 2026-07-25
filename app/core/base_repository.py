"""Repositorio base generico para operacoes CRUD."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from app.core.base import Base
from app.core.database import get_session

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repositorio base com CRUD generico, reaproveitado pelas entidades."""

    model: type[ModelType]

    def create(self, payload: dict[str, Any]) -> ModelType:
        """Cria um registro no banco."""
        with get_session() as session:
            registro = self.model(**payload)
            session.add(registro)
            session.flush()
            session.refresh(registro)
            session.expunge(registro)
            return registro

    def get_by_id(self, entity_id: Any) -> ModelType | None:
        """Busca um registro por id (suporta PK simples ou composta via tupla)."""
        with get_session() as session:
            registro = session.get(self.model, entity_id)
            if registro is not None:
                session.expunge(registro)
            return registro

    def list(self, filters: dict[str, Any] | None = None) -> list[ModelType]:
        """Lista registros com filtros opcionais."""
        with get_session() as session:
            query = session.query(self.model)
            if filters:
                query = query.filter_by(**filters)
            registros = query.all()
            for registro in registros:
                session.expunge(registro)
            return registros

    def update(self, entity_id: Any, payload: dict[str, Any]) -> ModelType | None:
        """Atualiza um registro existente."""
        with get_session() as session:
            registro = session.get(self.model, entity_id)
            if registro is None:
                return None
            for campo, valor in payload.items():
                setattr(registro, campo, valor)
            session.flush()
            session.refresh(registro)
            session.expunge(registro)
            return registro

    def delete(self, entity_id: Any) -> bool:
        """Remove um registro por id."""
        with get_session() as session:
            registro = session.get(self.model, entity_id)
            if registro is None:
                return False
            session.delete(registro)
            return True