"""Regras de negocio do dominio estoque."""

from __future__ import annotations

from app.estoque.repository import EstoqueRepository


class EstoqueService:
    """Camada de orquestracao das regras de negocio."""

    def __init__(self, repository: EstoqueRepository | None = None) -> None:
        self.repository = repository or EstoqueRepository()

    def register_entry_from_purchase(self, id_compra: int) -> None:
        """Called by Compras after a purchase is registered.

        Stock persistence stays in this module. No-op until inventory is implemented,
        so the purchases flow is not blocked.
        """
        return None

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
