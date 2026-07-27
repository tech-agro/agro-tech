"""Regras de negocio do dominio financeiro."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from app.core.database import pg_connector
from app.financeiro.enum import StatusContaReceber
from app.financeiro.models import ContaReceberModel
from app.financeiro.repository import FinanceiroRepository

logger = logging.getLogger(__name__)


class FinanceiroService:
    """Camada de orquestracao das regras de negocio."""

    def __init__(self, repository: FinanceiroRepository | None = None) -> None:
        self.repository = repository or FinanceiroRepository(pg_connector, logger)

    # ------------------------------------------------------------------
    # Hooks chamados por outros modulos
    # ------------------------------------------------------------------

    def receber_venda_confirmada(
        self, id_venda: int, valor: Decimal, data_venda: date | None = None, conn=None
    ) -> ContaReceberModel:
        """Chamado pela Comercial quando uma venda e confirmada: cria a conta a
        receber correspondente.

        Simplificacao assumida: vencimento = data da venda (a vista), ja que o
        schema atual nao modela prazo/condicao de pagamento por cliente.
        """
        conta = self.repository.create_conta_receber(
            id_venda=id_venda,
            valor=valor,
            vencimento=data_venda,
            status=StatusContaReceber.ABERTA,
            conn=conn,
        )
        if conta is None:
            raise ValueError("Nao foi possivel registrar a conta a receber da venda.")
        return conta
