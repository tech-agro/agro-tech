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
from app.manutencao.schemas.manutencao import (
    ManutencaoCreateSchema,
    ManutencaoReadSchema,
    ManutencaoUpdateSchema,
)
from app.manutencao.schemas.manutencao_corretiva import (
    ManutencaoCorretivaReadSchema,
    ManutencaoCorretivaUpdateSchema,
)
from app.manutencao.schemas.manutencao_preventiva import ManutencaoPreventivaReadSchema
from app.manutencao.schemas.ordem_servico import (
    OrdemServicoCreateSchema,
    OrdemServicoReadSchema,
    OrdemServicoUpdateSchema,
)
from app.manutencao.schemas.plano_manutencao import PlanoManutencaoReadSchema


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
    # Manutencao
    # ------------------------------------------------------------------

    def get_manutencao_by_id(self, id_manutencao: int) -> ManutencaoReadSchema | None:
        sql = text(
            """
            select id_manutencao, id_maquina, id_funcionario, id_prestador,
                   tipo, custo, status, dt_inicio, dt_fim
            from manutencao
            where id_manutencao = :id_manutencao
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_manutencao": id_manutencao}).fetchone()
            if row is None:
                return None
            return self._row_to_manutencao(row)
        except Exception as exc:
            self.logger.error("Erro ao buscar manutencao %s: %s", id_manutencao, exc)
            return None

    def update_manutencao(
        self,
        id_manutencao: int,
        payload: ManutencaoUpdateSchema,
    ) -> ManutencaoReadSchema | None:
        sql = text(
            """
            update manutencao
            set id_maquina = coalesce(:id_maquina, id_maquina),
                id_funcionario = coalesce(:id_funcionario, id_funcionario),
                id_prestador = coalesce(:id_prestador, id_prestador),
                tipo = coalesce(:tipo, tipo),
                custo = coalesce(:custo, custo),
                status = coalesce(:status, status),
                dt_inicio = coalesce(:dt_inicio, dt_inicio),
                dt_fim = coalesce(:dt_fim, dt_fim)
            where id_manutencao = :id_manutencao
            returning id_manutencao, id_maquina, id_funcionario, id_prestador,
                      tipo, custo, status, dt_inicio, dt_fim
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    sql,
                    {
                        "id_manutencao": id_manutencao,
                        "id_maquina": payload.id_maquina,
                        "id_funcionario": payload.id_funcionario,
                        "id_prestador": payload.id_prestador,
                        "tipo": payload.tipo,
                        "custo": payload.custo,
                        "status": payload.status,
                        "dt_inicio": payload.dt_inicio,
                        "dt_fim": payload.dt_fim,
                    },
                ).fetchone()
            if row is None:
                return None
            return self._row_to_manutencao(row)
        except Exception as exc:
            self.logger.error(
                "Erro ao atualizar manutencao %s: %s",
                id_manutencao,
                exc,
            )
            return None

    def count_open_manutencoes_by_maquina(
        self,
        id_maquina: int,
        *,
        exclude_id: int | None = None,
    ) -> int:
        params: dict[str, int] = {"id_maquina": id_maquina}
        exclude_clause = ""
        if exclude_id is not None:
            exclude_clause = "and id_manutencao <> :exclude_id"
            params["exclude_id"] = exclude_id

        sql = text(
            f"""
            select count(*)
            from manutencao
            where id_maquina = :id_maquina
              and status in ('ABERTA', 'EM_EXECUCAO')
              {exclude_clause}
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return conn.execute(sql, params).scalar_one()
        except Exception as exc:
            self.logger.error(
                "Erro ao contar manutencoes abertas da maquina %s: %s",
                id_maquina,
                exc,
            )
            return 0

    def get_plano_by_id(self, id_plano: int) -> PlanoManutencaoReadSchema | None:
        sql = text(
            """
            select id_plano, id_maquina, periodicidade, proxima_execucao
            from plano_manutencao
            where id_plano = :id_plano
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_plano": id_plano}).fetchone()
            if row is None:
                return None
            return self._row_to_plano(row)
        except Exception as exc:
            self.logger.error("Erro ao buscar plano %s: %s", id_plano, exc)
            return None

    def update_plano_proxima_execucao(
        self,
        id_plano: int,
        proxima_execucao,
    ) -> bool:
        sql = text(
            """
            update plano_manutencao
            set proxima_execucao = :proxima_execucao
            where id_plano = :id_plano
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                result = conn.execute(
                    sql,
                    {"id_plano": id_plano, "proxima_execucao": proxima_execucao},
                )
            return result.rowcount > 0
        except Exception as exc:
            self.logger.error(
                "Erro ao atualizar proxima execucao do plano %s: %s",
                id_plano,
                exc,
            )
            return False

    def create_manutencao_preventiva(
        self,
        manutencao: ManutencaoCreateSchema,
        *,
        id_plano: int,
        hodometro_execucao: float | None = None,
        proxima_hodometro: float | None = None,
    ) -> tuple[ManutencaoReadSchema, ManutencaoPreventivaReadSchema] | None:
        insert_manutencao = text(
            """
            insert into manutencao (
                id_maquina, id_funcionario, id_prestador, tipo, custo, status,
                dt_inicio, dt_fim
            )
            values (
                :id_maquina, :id_funcionario, :id_prestador, :tipo, :custo, :status,
                :dt_inicio, :dt_fim
            )
            returning id_manutencao, id_maquina, id_funcionario, id_prestador,
                      tipo, custo, status, dt_inicio, dt_fim
            """
        )
        insert_preventiva = text(
            """
            insert into manutencao_preventiva (
                id_manutencao, id_plano, hodometro_execucao, proxima_hodometro
            )
            values (
                :id_manutencao, :id_plano, :hodometro_execucao, :proxima_hodometro
            )
            returning id_manutencao, id_plano, hodometro_execucao, proxima_hodometro
            """
        )
        update_maquina = text(
            """
            update maquina
            set status = 'EM_MANUTENCAO'
            where id_maquina = :id_maquina
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                manutencao_row = conn.execute(
                    insert_manutencao,
                    {
                        "id_maquina": manutencao.id_maquina,
                        "id_funcionario": manutencao.id_funcionario,
                        "id_prestador": manutencao.id_prestador,
                        "tipo": manutencao.tipo,
                        "custo": manutencao.custo,
                        "status": manutencao.status,
                        "dt_inicio": manutencao.dt_inicio,
                        "dt_fim": manutencao.dt_fim,
                    },
                ).one()
                preventiva_row = conn.execute(
                    insert_preventiva,
                    {
                        "id_manutencao": manutencao_row.id_manutencao,
                        "id_plano": id_plano,
                        "hodometro_execucao": hodometro_execucao,
                        "proxima_hodometro": proxima_hodometro,
                    },
                ).one()
                conn.execute(update_maquina, {"id_maquina": manutencao.id_maquina})
            return (
                self._row_to_manutencao(manutencao_row),
                self._row_to_manutencao_preventiva(preventiva_row),
            )
        except Exception as exc:
            self.logger.error("Erro ao criar manutencao preventiva: %s", exc)
            return None

    def create_manutencao_corretiva(
        self,
        manutencao: ManutencaoCreateSchema,
        *,
        defeito_relatado: str,
        causa_raiz: str | None = None,
        solucao_aplicada: str | None = None,
    ) -> tuple[ManutencaoReadSchema, ManutencaoCorretivaReadSchema] | None:
        insert_manutencao = text(
            """
            insert into manutencao (
                id_maquina, id_funcionario, id_prestador, tipo, custo, status,
                dt_inicio, dt_fim
            )
            values (
                :id_maquina, :id_funcionario, :id_prestador, :tipo, :custo, :status,
                :dt_inicio, :dt_fim
            )
            returning id_manutencao, id_maquina, id_funcionario, id_prestador,
                      tipo, custo, status, dt_inicio, dt_fim
            """
        )
        insert_corretiva = text(
            """
            insert into manutencao_corretiva (
                id_manutencao, defeito_relatado, causa_raiz, solucao_aplicada
            )
            values (
                :id_manutencao, :defeito_relatado, :causa_raiz, :solucao_aplicada
            )
            returning id_manutencao, defeito_relatado, causa_raiz, solucao_aplicada
            """
        )
        update_maquina = text(
            """
            update maquina
            set status = 'EM_MANUTENCAO'
            where id_maquina = :id_maquina
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                manutencao_row = conn.execute(
                    insert_manutencao,
                    {
                        "id_maquina": manutencao.id_maquina,
                        "id_funcionario": manutencao.id_funcionario,
                        "id_prestador": manutencao.id_prestador,
                        "tipo": manutencao.tipo,
                        "custo": manutencao.custo,
                        "status": manutencao.status,
                        "dt_inicio": manutencao.dt_inicio,
                        "dt_fim": manutencao.dt_fim,
                    },
                ).one()
                corretiva_row = conn.execute(
                    insert_corretiva,
                    {
                        "id_manutencao": manutencao_row.id_manutencao,
                        "defeito_relatado": defeito_relatado,
                        "causa_raiz": causa_raiz,
                        "solucao_aplicada": solucao_aplicada,
                    },
                ).one()
                conn.execute(update_maquina, {"id_maquina": manutencao.id_maquina})
            return (
                self._row_to_manutencao(manutencao_row),
                self._row_to_manutencao_corretiva(corretiva_row),
            )
        except Exception as exc:
            self.logger.error("Erro ao criar manutencao corretiva: %s", exc)
            return None

    def get_manutencao_preventiva_by_id(
        self,
        id_manutencao: int,
    ) -> ManutencaoPreventivaReadSchema | None:
        sql = text(
            """
            select id_manutencao, id_plano, hodometro_execucao, proxima_hodometro
            from manutencao_preventiva
            where id_manutencao = :id_manutencao
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_manutencao": id_manutencao}).fetchone()
            if row is None:
                return None
            return self._row_to_manutencao_preventiva(row)
        except Exception as exc:
            self.logger.error(
                "Erro ao buscar manutencao preventiva %s: %s",
                id_manutencao,
                exc,
            )
            return None

    def get_manutencao_corretiva_by_id(
        self,
        id_manutencao: int,
    ) -> ManutencaoCorretivaReadSchema | None:
        sql = text(
            """
            select id_manutencao, defeito_relatado, causa_raiz, solucao_aplicada
            from manutencao_corretiva
            where id_manutencao = :id_manutencao
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_manutencao": id_manutencao}).fetchone()
            if row is None:
                return None
            return self._row_to_manutencao_corretiva(row)
        except Exception as exc:
            self.logger.error(
                "Erro ao buscar manutencao corretiva %s: %s",
                id_manutencao,
                exc,
            )
            return None

    def update_manutencao_corretiva(
        self,
        id_manutencao: int,
        payload: ManutencaoCorretivaUpdateSchema,
    ) -> ManutencaoCorretivaReadSchema | None:
        sql = text(
            """
            update manutencao_corretiva
            set defeito_relatado = coalesce(:defeito_relatado, defeito_relatado),
                causa_raiz = coalesce(:causa_raiz, causa_raiz),
                solucao_aplicada = coalesce(:solucao_aplicada, solucao_aplicada)
            where id_manutencao = :id_manutencao
            returning id_manutencao, defeito_relatado, causa_raiz, solucao_aplicada
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    sql,
                    {
                        "id_manutencao": id_manutencao,
                        "defeito_relatado": payload.defeito_relatado,
                        "causa_raiz": payload.causa_raiz,
                        "solucao_aplicada": payload.solucao_aplicada,
                    },
                ).fetchone()
            if row is None:
                return None
            return self._row_to_manutencao_corretiva(row)
        except Exception as exc:
            self.logger.error(
                "Erro ao atualizar manutencao corretiva %s: %s",
                id_manutencao,
                exc,
            )
            return None

    def set_maquina_status(self, id_maquina: int, status: str) -> bool:
        sql = text(
            """
            update maquina
            set status = :status
            where id_maquina = :id_maquina
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                result = conn.execute(
                    sql,
                    {"id_maquina": id_maquina, "status": status},
                )
            return result.rowcount > 0
        except Exception as exc:
            self.logger.error(
                "Erro ao atualizar status da maquina %s: %s",
                id_maquina,
                exc,
            )
            return False

    def count_open_ordens_by_manutencao(self, id_manutencao: int) -> int:
        sql = text(
            """
            select count(*)
            from ordem_servico
            where id_manutencao = :id_manutencao
              and status in ('ABERTA', 'EM_EXECUCAO')
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return conn.execute(sql, {"id_manutencao": id_manutencao}).scalar_one()
        except Exception as exc:
            self.logger.error(
                "Erro ao contar ordens abertas da manutencao %s: %s",
                id_manutencao,
                exc,
            )
            return 0

    def finalize_manutencao_execution(
        self,
        id_manutencao: int,
        *,
        id_maquina: int,
        custo: float | None,
        dt_fim,
        observacao_historico: str,
        id_plano: int | None = None,
        proxima_execucao=None,
        proxima_hodometro: float | None = None,
    ) -> ManutencaoReadSchema | None:
        """Conclui manutencao e registra historico, financeiro e ciclos preventivos."""
        update_manutencao = text(
            """
            update manutencao
            set status = 'CONCLUIDA',
                custo = :custo,
                dt_fim = :dt_fim
            where id_manutencao = :id_manutencao
            returning id_manutencao, id_maquina, id_funcionario, id_prestador,
                      tipo, custo, status, dt_inicio, dt_fim
            """
        )
        insert_historico = text(
            """
            insert into historico_manutencao (id_manutencao, observacao)
            values (:id_manutencao, :observacao)
            """
        )
        insert_fluxo = text(
            """
            insert into fluxo_caixa (valor, tipo, data_movimento)
            values (:valor, :tipo, :data_movimento)
            """
        )
        update_plano = text(
            """
            update plano_manutencao
            set proxima_execucao = :proxima_execucao
            where id_plano = :id_plano
            """
        )
        update_preventiva_hodometro = text(
            """
            update manutencao_preventiva
            set proxima_hodometro = :proxima_hodometro
            where id_manutencao = :id_manutencao
            """
        )
        count_open_manutencoes = text(
            """
            select count(*)
            from manutencao
            where id_maquina = :id_maquina
              and status in ('ABERTA', 'EM_EXECUCAO')
            """
        )
        update_maquina_disponivel = text(
            """
            update maquina
            set status = 'DISPONIVEL'
            where id_maquina = :id_maquina
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(
                    update_manutencao,
                    {
                        "id_manutencao": id_manutencao,
                        "custo": custo,
                        "dt_fim": dt_fim,
                    },
                ).fetchone()
                if row is None:
                    return None

                conn.execute(
                    insert_historico,
                    {
                        "id_manutencao": id_manutencao,
                        "observacao": observacao_historico,
                    },
                )

                if custo is not None and custo > 0:
                    conn.execute(
                        insert_fluxo,
                        {
                            "valor": custo,
                            "tipo": f"CUSTO_MANUTENCAO:{id_manutencao}",
                            "data_movimento": dt_fim,
                        },
                    )

                if id_plano is not None and proxima_execucao is not None:
                    conn.execute(
                        update_plano,
                        {
                            "id_plano": id_plano,
                            "proxima_execucao": proxima_execucao,
                        },
                    )

                if proxima_hodometro is not None:
                    conn.execute(
                        update_preventiva_hodometro,
                        {
                            "id_manutencao": id_manutencao,
                            "proxima_hodometro": proxima_hodometro,
                        },
                    )

                abertas = conn.execute(
                    count_open_manutencoes,
                    {"id_maquina": id_maquina},
                ).scalar_one()
                if abertas == 0:
                    conn.execute(update_maquina_disponivel, {"id_maquina": id_maquina})

            return self._row_to_manutencao(row)
        except Exception as exc:
            self.logger.error(
                "Erro ao finalizar execucao da manutencao %s: %s",
                id_manutencao,
                exc,
            )
            return None

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

    @staticmethod
    def _row_to_manutencao(row) -> ManutencaoReadSchema:
        return ManutencaoReadSchema(
            id_manutencao=row.id_manutencao,
            id_maquina=row.id_maquina,
            id_funcionario=row.id_funcionario,
            id_prestador=row.id_prestador,
            tipo=row.tipo,
            custo=float(row.custo) if row.custo is not None else None,
            status=row.status,
            dt_inicio=row.dt_inicio,
            dt_fim=row.dt_fim,
        )

    @staticmethod
    def _row_to_manutencao_preventiva(row) -> ManutencaoPreventivaReadSchema:
        return ManutencaoPreventivaReadSchema(
            id_manutencao=row.id_manutencao,
            id_plano=row.id_plano,
            hodometro_execucao=(
                float(row.hodometro_execucao)
                if row.hodometro_execucao is not None
                else None
            ),
            proxima_hodometro=(
                float(row.proxima_hodometro)
                if row.proxima_hodometro is not None
                else None
            ),
        )

    @staticmethod
    def _row_to_manutencao_corretiva(row) -> ManutencaoCorretivaReadSchema:
        return ManutencaoCorretivaReadSchema(
            id_manutencao=row.id_manutencao,
            defeito_relatado=row.defeito_relatado,
            causa_raiz=row.causa_raiz,
            solucao_aplicada=row.solucao_aplicada,
        )

    @staticmethod
    def _row_to_plano(row) -> PlanoManutencaoReadSchema:
        return PlanoManutencaoReadSchema(
            id_plano=row.id_plano,
            id_maquina=row.id_maquina,
            periodicidade=row.periodicidade,
            proxima_execucao=row.proxima_execucao,
        )
