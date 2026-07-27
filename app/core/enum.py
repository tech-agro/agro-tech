"""Enums reutilizados entre os módulos do sistema."""

from enum import Enum

class StatusCertificacao(str, Enum):
    VIGENTE = "VIGENTE"
    VENCIDA = "VENCIDA"
    SUSPENSA = "SUSPENSA"
    CANCELADA = "CANCELADA"