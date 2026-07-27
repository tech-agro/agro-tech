"""Regras de negocio do dominio logistica."""

from __future__ import annotations

from app.logistica.repository import LogisticaRepository

class LogisticaService:
    """Camada de orquestracao das regras de negocio."""

    def __init__(self, repository: LogisticaRepository | None = None) -> None:
        self.repository = repository or LogisticaRepository()

    # ------------------------------------------------------------------
    # Hooks chamados por outros modulos
    # ------------------------------------------------------------------

    def receber_venda_confirmada(self, id_venda: int) -> None:
        """Chamado pela Comercial quando uma venda e confirmada.

        Implementacao futura:
            - abrir uma `operacao_logistica` (ordem de carregamento) vinculada
              a venda, com veiculo e rota a definir.

        Mantido como placeholder ate a implementacao do modulo Logistica.
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
