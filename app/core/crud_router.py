"""Factory de rotas CRUD genericas para FastAPI."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.base_service import BaseService


def build_crud_router(
    *,
    service: BaseService,
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    read_schema: type[BaseModel],
    prefix: str,
    not_found_message: str,
    id_type: type = int,
) -> APIRouter:
    """Monta um APIRouter com as 5 rotas CRUD padrao para uma entidade."""
    router = APIRouter(prefix=prefix)

    @router.post("/", response_model=read_schema)
    def create(payload: create_schema) -> Any:  # type: ignore[valid-type]
        return service.create(payload)

    @router.get("/{entity_id}", response_model=read_schema)
    def get(entity_id: id_type) -> Any:  # type: ignore[valid-type]
        resultado = service.get_by_id(entity_id)
        if resultado is None:
            raise HTTPException(status_code=404, detail=not_found_message)
        return resultado

    @router.get("/", response_model=list[read_schema])
    def list_all() -> Any:
        return service.list()

    @router.patch("/{entity_id}", response_model=read_schema)
    def update(entity_id: id_type, payload: update_schema) -> Any:  # type: ignore[valid-type]
        resultado = service.update(entity_id, payload)
        if resultado is None:
            raise HTTPException(status_code=404, detail=not_found_message)
        return resultado

    @router.delete("/{entity_id}", status_code=204)
    def delete(entity_id: id_type) -> None:
        if not service.delete(entity_id):
            raise HTTPException(status_code=404, detail=not_found_message)

    return router