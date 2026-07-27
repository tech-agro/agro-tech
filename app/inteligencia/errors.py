"""Erros de regras de negocio do dominio inteligencia."""


class InteligenciaError(Exception):
    """Violacao de regra de negocio."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InteligenciaNotFoundError(InteligenciaError):
    """Registro nao encontrado."""


class InteligenciaValidationError(InteligenciaError):
    """Entrada ou operacao invalida."""


class InteligenciaConflictError(InteligenciaError):
    """Conflito com estado existente (ex.: duplicidade)."""
