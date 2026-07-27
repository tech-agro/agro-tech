"""Service base generico para operacoes CRUD."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.core.base_repository import BaseRepository

ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)


class BaseService(Generic[ReadSchemaType]):
    """Service base com CRUD generico, reaproveitado pelas entidades."""

    def __init__(self, repository: BaseRepository, read_schema: type[ReadSchemaType]) -> None:
        self.repository = repository
        self.read_schema = read_schema

    def create(self, payload: BaseModel) -> ReadSchemaType:
        registro = self.repository.create(payload.model_dump())
        return self.read_schema.model_validate(registro)

    def get_by_id(self, entity_id: Any) -> ReadSchemaType | None:
        registro = self.repository.get_by_id(entity_id)
        if registro is None:
            return None
        return self.read_schema.model_validate(registro)

    def list(self, filters: dict[str, Any] | None = None) -> list[ReadSchemaType]:
        registros = self.repository.list(filters)
        return [self.read_schema.model_validate(r) for r in registros]

    def update(self, entity_id: Any, payload: BaseModel) -> ReadSchemaType | None:
        dados = payload.model_dump(exclude_unset=True)
        registro = self.repository.update(entity_id, dados)
        if registro is None:
            return None
        return self.read_schema.model_validate(registro)

    def delete(self, entity_id: Any) -> bool:
        return self.repository.delete(entity_id)