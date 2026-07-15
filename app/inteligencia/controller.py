"""Recebe requisicoes da interface para o dominio inteligencia."""

from __future__ import annotations

from app.inteligencia.service import InteligenciaService

class InteligenciaController:
    """Adaptador entre interface e service."""

    def __init__(self, service: InteligenciaService | None = None) -> None:
        self.service = service or InteligenciaService()

    def create(self, payload):
        return self.service.create(payload)

    def get_by_id(self, entity_id: int):
        return self.service.get_by_id(entity_id)

    def list(self, filters=None):
        return self.service.list(filters)

    def update(self, entity_id: int, payload):
        return self.service.update(entity_id, payload)

    def delete(self, entity_id: int):
        return self.service.delete(entity_id)
