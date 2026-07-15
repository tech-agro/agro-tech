"""Recebe requisicoes da interface para o dominio manutencao."""

from __future__ import annotations

from app.manutencao.service import ManutencaoService

class ManutencaoController:
    """Adaptador entre interface e service."""

    def __init__(self, service: ManutencaoService | None = None) -> None:
        self.service = service or ManutencaoService()

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
