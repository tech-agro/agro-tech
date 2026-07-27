"""Acesso a dados do dominio manutencao."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from app.core.database import pg_connector as default_pg_connector
from app.manutencao.schemas.maquina import (
    MaquinaCreateSchema,
    MaquinaReadSchema,
    MaquinaUpdateSchema,
)
from app.manutencao.schemas.ordem_servico import (
    OrdemServicoCreateSchema,
    OrdemServicoReadSchema,
    OrdemServicoUpdateSchema,
)


@dataclass(slots=True)
class MaquinaFilters:
    id_tipo_maquina: int | None = None
    id_fazenda: int | None = None
    status: str | None = None
    nome: str | None = None


@dataclass(slots=True)
class OrdemServicoFilters:
    id_manutencao: int | None = None
    id_maquina: int | None = None
    status: str | None = None


class ManutencaoRepository:
    """Repositorio para CRUD e consultas de maquinas e ordens de servico."""

    def __init__(self, pg_connector=None, logger: logging.Logger | None = None) -> None:
        self.pg_connector = pg_connector or default_pg_connector
        self.logger = logger or logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Maquina
    # ------------------------------------------------------------------

    def create_maquina(
        self,
        payload: MaquinaCreateSchema,
        *,
        id_fazenda: int,
    ) -> MaquinaReadSchema | None:
        sql = text(
            """
            insert into maquina (id_tipo_maquina, id_fazenda, nome, status)
            values (:id_tipo_maquina, :id_fazenda, :nome, :status)
            returning id_maquina, id_tipo_maquina, nome, status
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    sql,
                    {
                        "id_tipo_maquina": payload.id_tipo_maquina,
                        "id_fazenda": id_fazenda,
                        "nome": payload.nome,
                        "status": payload.status,
                    },
                ).one()
            return self._row_to_maquina(row)
        except Exception as exc:
            self.logger.error("Erro ao criar maquina: %s", exc)
            return None

    def get_maquina_by_id(self, id_maquina: int) -> MaquinaReadSchema | None:
        sql = text(
            """
            select id_maquina, id_tipo_maquina, nome, status
            from maquina
            where id_maquina = :id_maquina
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_maquina": id_maquina}).fetchone()
            if row is None:
                return None
            return self._row_to_maquina(row)
        except Exception as exc:
            self.logger.error("Erro ao buscar maquina %s: %s", id_maquina, exc)
            return None

    def list_maquinas(
        self,
        filters: MaquinaFilters | None = None,
    ) -> list[MaquinaReadSchema]:
        filters = filters or MaquinaFilters()
        clauses = ["1 = 1"]
        params: dict[str, Any] = {}

        if filters.id_tipo_maquina is not None:
            clauses.append("id_tipo_maquina = :id_tipo_maquina")
            params["id_tipo_maquina"] = filters.id_tipo_maquina
        if filters.id_fazenda is not None:
            clauses.append("id_fazenda = :id_fazenda")
            params["id_fazenda"] = filters.id_fazenda
        if filters.status is not None:
            clauses.append("status = :status")
            params["status"] = filters.status
        if filters.nome is not None:
            clauses.append("nome ilike :nome")
            params["nome"] = f"%{filters.nome}%"

        sql = text(
            f"""
            select id_maquina, id_tipo_maquina, nome, status
            from maquina
            where {' and '.join(clauses)}
            order by nome
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                rows = conn.execute(sql, params).fetchall()
            return [self._row_to_maquina(row) for row in rows]
        except Exception as exc:
            self.logger.error("Erro ao listar maquinas: %s", exc)
            return []

    def update_maquina(
        self,
        id_maquina: int,
        payload: MaquinaUpdateSchema,
    ) -> MaquinaReadSchema | None:
        sql = text(
            """
            update maquina
            set id_tipo_maquina = coalesce(:id_tipo_maquina, id_tipo_maquina),
                nome = coalesce(:nome, nome),
                status = coalesce(:status, status)
            where id_maquina = :id_maquina
            returning id_maquina, id_tipo_maquina, nome, status
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    sql,
                    {
                        "id_maquina": id_maquina,
                        "id_tipo_maquina": payload.id_tipo_maquina,
                        "nome": payload.nome,
                        "status": payload.status,
                    },
                ).fetchone()
            if row is None:
                return None
            return self._row_to_maquina(row)
        except Exception as exc:
            self.logger.error("Erro ao atualizar maquina %s: %s", id_maquina, exc)
            return None

    def delete_maquina(self, id_maquina: int) -> bool:
        sql = text("delete from maquina where id_maquina = :id_maquina")
        try:
            with self.pg_connector.pool.begin() as conn:
                result = conn.execute(sql, {"id_maquina": id_maquina})
            return result.rowcount > 0
        except Exception as exc:
            self.logger.error("Erro ao excluir maquina %s: %s", id_maquina, exc)
            return False

    # ------------------------------------------------------------------
    # Ordem de servico
    # ------------------------------------------------------------------

    def create_ordem_servico(
        self,
        payload: OrdemServicoCreateSchema,
    ) -> OrdemServicoReadSchema | None:
        sql = text(
            """
            insert into ordem_servico (id_manutencao, descricao, status)
            values (:id_manutencao, :descricao, :status)
            returning id_ordem_servico, id_manutencao, descricao, status
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    sql,
                    {
                        "id_manutencao": payload.id_manutencao,
                        "descricao": payload.descricao,
                        "status": payload.status,
                    },
                ).one()
            return self._row_to_ordem_servico(row)
        except Exception as exc:
            self.logger.error("Erro ao criar ordem de servico: %s", exc)
            return None

    def get_ordem_servico_by_id(
        self,
        id_ordem_servico: int,
    ) -> OrdemServicoReadSchema | None:
        sql = text(
            """
            select id_ordem_servico, id_manutencao, descricao, status
            from ordem_servico
            where id_ordem_servico = :id_ordem_servico
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    sql,
                    {"id_ordem_servico": id_ordem_servico},
                ).fetchone()
            if row is None:
                return None
            return self._row_to_ordem_servico(row)
        except Exception as exc:
            self.logger.error(
                "Erro ao buscar ordem de servico %s: %s",
                id_ordem_servico,
                exc,
            )
            return None

    def list_ordens_servico(
        self,
        filters: OrdemServicoFilters | None = None,
    ) -> list[OrdemServicoReadSchema]:
        filters = filters or OrdemServicoFilters()
        clauses = ["1 = 1"]
        params: dict[str, Any] = {}
        join = ""

        if filters.id_maquina is not None:
            join = "join manutencao m on m.id_manutencao = os.id_manutencao"
            clauses.append("m.id_maquina = :id_maquina")
            params["id_maquina"] = filters.id_maquina
        if filters.id_manutencao is not None:
            clauses.append("os.id_manutencao = :id_manutencao")
            params["id_manutencao"] = filters.id_manutencao
        if filters.status is not None:
            clauses.append("os.status = :status")
            params["status"] = filters.status

        sql = text(
            f"""
            select os.id_ordem_servico, os.id_manutencao, os.descricao, os.status
            from ordem_servico os
            {join}
            where {' and '.join(clauses)}
            order by os.id_ordem_servico desc
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                rows = conn.execute(sql, params).fetchall()
            return [self._row_to_ordem_servico(row) for row in rows]
        except Exception as exc:
            self.logger.error("Erro ao listar ordens de servico: %s", exc)
            return []

    def update_ordem_servico(
        self,
        id_ordem_servico: int,
        payload: OrdemServicoUpdateSchema,
    ) -> OrdemServicoReadSchema | None:
        sql = text(
            """
            update ordem_servico
            set id_manutencao = coalesce(:id_manutencao, id_manutencao),
                descricao = coalesce(:descricao, descricao),
                status = coalesce(:status, status)
            where id_ordem_servico = :id_ordem_servico
            returning id_ordem_servico, id_manutencao, descricao, status
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    sql,
                    {
                        "id_ordem_servico": id_ordem_servico,
                        "id_manutencao": payload.id_manutencao,
                        "descricao": payload.descricao,
                        "status": payload.status,
                    },
                ).fetchone()
            if row is None:
                return None
            return self._row_to_ordem_servico(row)
        except Exception as exc:
            self.logger.error(
                "Erro ao atualizar ordem de servico %s: %s",
                id_ordem_servico,
                exc,
            )
            return None

    def delete_ordem_servico(self, id_ordem_servico: int) -> bool:
        sql = text(
            "delete from ordem_servico where id_ordem_servico = :id_ordem_servico"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                result = conn.execute(
                    sql,
                    {"id_ordem_servico": id_ordem_servico},
                )
            return result.rowcount > 0
        except Exception as exc:
            self.logger.error(
                "Erro ao excluir ordem de servico %s: %s",
                id_ordem_servico,
                exc,
            )
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_maquina(row) -> MaquinaReadSchema:
        return MaquinaReadSchema(
            id_maquina=row.id_maquina,
            id_tipo_maquina=row.id_tipo_maquina,
            nome=row.nome,
            status=row.status,
        )

    @staticmethod
    def _row_to_ordem_servico(row) -> OrdemServicoReadSchema:
        return OrdemServicoReadSchema(
            id_ordem_servico=row.id_ordem_servico,
            id_manutencao=row.id_manutencao,
            descricao=row.descricao,
            status=row.status,
        )
