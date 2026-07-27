"""Exceções do domínio financeiro."""

from __future__ import annotations

class FinanceiroError(Exception):
    """Erro de negócio do módulo financeiro."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)