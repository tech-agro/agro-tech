"""Acesso a dados do dominio financeiro."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.core.database import pg_connector as default_pg_connector
from app.financeiro.enum import StatusContaReceber
from app.financeiro.models import ContaReceberModel


class FinanceiroRepository:
    """Repositorio para integracoes financeiras."""

    def __init__(self, pg_connector=None, logger: logging.Logger | None = None) -> None:
        self.pg_connector = pg_connector or default_pg_connector
        self.logger = logger or logging.getLogger(__name__)

    @contextmanager
    def _connection(self, conn=None):
        """Reutiliza uma conexao/transacao existente (para escritas compostas,
        ex. dentro da transacao de ComercialService.registrar_venda) ou abre
        uma nova."""
        if conn is not None:
            yield conn
        else:
            with self.pg_connector.pool.begin() as new_conn:
                yield new_conn

    def create_conta_receber(
        self,
        id_venda: int,
        valor: Decimal,
        vencimento: date | None,
        status: StatusContaReceber,
        conn=None,
    ) -> ContaReceberModel | None:
        sql = text(
            """
            insert into conta_receber (id_venda, valor, vencimento, status)
            values (:id_venda, :valor, :vencimento, :status)
            returning id_conta_receber
            """
        )
        try:
            with self._connection(conn) as c:
                id_conta_receber = c.execute(
                    sql,
                    {"id_venda": id_venda, "valor": valor, "vencimento": vencimento, "status": status.value},
                ).scalar_one()
                return ContaReceberModel(
                    id_conta_receber=id_conta_receber,
                    id_venda=id_venda,
                    valor=valor,
                    vencimento=vencimento,
                    status=status,
                )
        except Exception as e:
            self.logger.error(f"Error creating conta_receber: {e}")
            return None

    def registrar_custo_manutencao(
        self,
        id_manutencao: int,
        valor: float,
        data_movimento: date,
    ) -> bool:
        """Registra custo de manutencao no fluxo de caixa.

        Nao usado hoje: `ManutencaoRepository.finalize_manutencao_execution`
        (app/manutencao/repository.py) ja grava o mesmo `fluxo_caixa`
        diretamente, na mesma transacao que conclui a manutencao (atomico).
        Mantido por nao ser deste modulo a decisao de remover codigo alheio.
        """
        if valor <= 0:
            return False

        sql = text(
            """
            insert into fluxo_caixa (valor, tipo, data_movimento)
            values (:valor, :tipo, :data_movimento)
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(
                    sql,
                    {
                        "valor": valor,
                        "tipo": f"CUSTO_MANUTENCAO:{id_manutencao}",
                        "data_movimento": data_movimento,
                    },
                )
            return True
        except Exception as exc:
            self.logger.error(
                "Erro ao registrar custo da manutencao %s: %s",
                id_manutencao,
                exc,
            )
            return False
