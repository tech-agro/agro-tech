"""Enums utilizados pelo módulo financeiro."""

from enum import Enum


class StatusContaPagarEnum(str, Enum):
    """Status possíveis para uma conta a pagar."""

    ABERTA = "ABERTA"
    PARCIALMENTE_PAGA = "PARCIALMENTE_PAGA"
    PAGA = "PAGA"
    VENCIDA = "VENCIDA"
    CANCELADA = "CANCELADA"


class StatusContaReceberEnum(str, Enum):
    """Status possíveis para uma conta a receber."""

    ABERTA = "ABERTA"
    PARCIALMENTE_RECEBIDA = "PARCIALMENTE_RECEBIDA"
    RECEBIDA = "RECEBIDA"
    VENCIDA = "VENCIDA"
    CANCELADA = "CANCELADA"