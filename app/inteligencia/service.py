"""Regras de negocio do dominio inteligencia."""

from __future__ import annotations

from app.inteligencia.repository import InteligenciaRepository

class InteligenciaService:
    """Camada de orquestracao das regras de negocio."""

    def __init__(self, repository: InteligenciaRepository | None = None) -> None:
        self.repository = repository or InteligenciaRepository()

    def create(self, payload):
        """Valida entrada e delega persistencia ao repositorio."""
        raise NotImplementedError

    def get_by_id(self, entity_id: int):
        """Aplica regras de leitura do dominio."""
        raise NotImplementedError

    def list(self, filters=None):
        """Executa listagem com regras de negocio."""
        raise NotImplementedError

    def update(self, entity_id: int, payload):
        """Valida e aplica atualizacao do dominio."""
        raise NotImplementedError

    def delete(self, entity_id: int):
        """Valida e delega exclusao ao repositorio."""
        raise NotImplementedError
