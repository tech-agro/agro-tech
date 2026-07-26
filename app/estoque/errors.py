"""Exceções do domínio estoque."""

from __future__ import annotations


class EstoqueError(Exception):
    """Erro de regra de negócio do domínio estoque."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)