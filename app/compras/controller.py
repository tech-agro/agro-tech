"""Recebe requisicoes da interface para o dominio compras."""

from __future__ import annotations

from app.compras.service import ComprasService

class ComprasController:
    """Adaptador entre interface e service."""

    def __init__(self, service: ComprasService | None = None) -> None:
        self.service = service or ComprasService()

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
