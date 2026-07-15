"""Acesso a dados do dominio comercial."""

from __future__ import annotations

class ComercialRepository:
    """Repositorio base para CRUD e consultas do dominio."""

    def create(self, payload):
        """Cria um registro no banco."""
        raise NotImplementedError

    def get_by_id(self, entity_id: int):
        """Busca um registro por id."""
        raise NotImplementedError

    def list(self, filters=None):
        """Lista registros com filtros opcionais."""
        raise NotImplementedError

    def update(self, entity_id: int, payload):
        """Atualiza um registro existente."""
        raise NotImplementedError

    def delete(self, entity_id: int):
        """Remove um registro por id."""
        raise NotImplementedError
