"""Regras de negocio do dominio financeiro."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.core.database import get_session, pg_connector
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

    def register_logistics_cost(
        self,
        *,
        id_operacao: int,
        valor: Decimal | float,
        data_movimento: date | None = None,
        descricao: str | None = None,
    ) -> int | None:
        """Called by Logistics when an operation incurs cost.

        Persists a cash-flow row (tipo=custo_logistico). Full AP/AR documents
        remain out of scope until the financial module is completed.
        """
        amount = Decimal(str(valor))
        if amount <= 0:
            return None
        with get_session() as session:
            row = session.execute(
                text(
                    """
                    INSERT INTO fluxo_caixa (valor, tipo, data_movimento)
                    VALUES (:valor, :tipo, :data_movimento)
                    RETURNING id_fluxo
                    """
                ),
                {
                    "valor": amount,
                    "tipo": f"custo_logistico:op={id_operacao}"
                    + (f":{descricao}" if descricao else ""),
                    "data_movimento": data_movimento or date.today(),
                },
            ).first()
            return int(row[0]) if row is not None else None

    def register_phytosanitary_cost(
        self,
        *,
        id_aplicacao: int,
        valor: Decimal | float,
        data_movimento: date | None = None,
        descricao: str | None = None,
    ) -> int | None:
        """Called by Phytosanitary when a pesticide application incurs cost.

        Persists a cash-flow row (tipo=custo_fitossanitario). Full cost-center
        documents remain out of scope until the financial module is completed.
        """
        amount = Decimal(str(valor))
        if amount <= 0:
            return None
        with get_session() as session:
            row = session.execute(
                text(
                    """
                    INSERT INTO fluxo_caixa (valor, tipo, data_movimento)
                    VALUES (:valor, :tipo, :data_movimento)
                    RETURNING id_fluxo
                    """
                ),
                {
                    "valor": amount,
                    "tipo": f"custo_fitossanitario:app={id_aplicacao}"
                    + (f":{descricao}" if descricao else ""),
                    "data_movimento": data_movimento or date.today(),
                },
            ).first()
            return int(row[0]) if row is not None else None
