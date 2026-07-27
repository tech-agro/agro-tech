"""Acesso a dados do dominio financeiro."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import text

from app.core.database import pg_connector as default_pg_connector


class FinanceiroRepository:
    """Repositorio para integracoes financeiras."""

    def __init__(self, pg_connector=None, logger: logging.Logger | None = None) -> None:
        self.pg_connector = pg_connector or default_pg_connector
        self.logger = logger or logging.getLogger(__name__)

    def registrar_custo_manutencao(
        self,
        id_manutencao: int,
        valor: float,
        data_movimento: date,
    ) -> bool:
        """Registra custo de manutencao no fluxo de caixa."""
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
