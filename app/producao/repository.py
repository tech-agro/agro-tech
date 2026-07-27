from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from app.producao.enum import (
    StatusAtividadeAgricola,
    StatusColheita,
    StatusOperacaoAgricola,
    StatusOrdemProducao,
    StatusPlanejamentoSafra,
    StatusPlantio,
    StatusSafra,
)
from app.producao.models import (
    AdubacaoModel,
    AnaliseSoloModel,
    AtividadeAgricolaModel,
    ColheitaModel,
    CondicaoClimaticaModel,
    CulturaModel,
    FazendaModel,
    FuncionarioAtividadeModel,
    IrrigacaoModel,
    MonitoramentoSafraModel,
    OperacaoAgricolaModel,
    OrdemProducaoModel,
    ParametroMonitoramentoModel,
    PlanejamentoSafraModel,
    PlantioModel,
    PulverizacaoModel,
    SafraModel,
    SoloModel,
    TalhaoModel,
)


class ProducaoRepository:
    def __init__(self, pg_connector, logger):
        self.pg_connector = pg_connector
        self.logger = logger

    @contextmanager
    def _connection(self, conn=None):
        """Reutiliza uma conexao/transacao existente (para escritas compostas) ou abre uma nova."""
        if conn is not None:
            yield conn
        else:
            with self.pg_connector.pool.begin() as new_conn:
                yield new_conn

    @staticmethod
    def _where_from_filters(filters: dict | None, allowed_columns: set[str]) -> tuple[str, dict]:
        clauses = []
        params = {}
        for key, value in (filters or {}).items():
            if key not in allowed_columns:
                continue
            clauses.append(f"{key} = :{key}")
            params[key] = value
        where_sql = f"where {' and '.join(clauses)}" if clauses else ""
        return where_sql, params

    # ------------------------------------------------------------------
    # Fazenda
    # ------------------------------------------------------------------
    def create_fazenda(self, nome: str, localizacao: str | None = None, conn=None) -> FazendaModel | None:
        sql = text("insert into fazenda (nome, localizacao) values (:nome, :localizacao) returning id_fazenda")
        try:
            with self._connection(conn) as c:
                id_fazenda = c.execute(sql, {"nome": nome, "localizacao": localizacao}).scalar_one()
                return FazendaModel(id_fazenda=id_fazenda, nome=nome, localizacao=localizacao)
        except Exception as e:
            self.logger.error(f"Error creating fazenda: {e}")
            return None

    def get_fazenda_by_id(self, id_fazenda: int) -> FazendaModel | None:
        sql = text("select id_fazenda, nome, localizacao from fazenda where id_fazenda = :id_fazenda")
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_fazenda": id_fazenda}).fetchone()
                return FazendaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching fazenda {id_fazenda}: {e}")
            return None

    def list_fazendas(self, filters: dict | None = None) -> list[FazendaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_fazenda", "nome", "localizacao"})
        sql = text(f"select id_fazenda, nome, localizacao from fazenda {where_sql} order by id_fazenda")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [FazendaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing fazendas: {e}")
            return []

    def update_fazenda(
        self, id_fazenda: int, nome: str | None = None, localizacao: str | None = None, conn=None
    ) -> bool:
        sql = text(
            """
            update fazenda
            set nome = coalesce(:nome, nome),
                localizacao = coalesce(:localizacao, localizacao)
            where id_fazenda = :id_fazenda
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"nome": nome, "localizacao": localizacao, "id_fazenda": id_fazenda})
            return True
        except Exception as e:
            self.logger.error(f"Error updating fazenda {id_fazenda}: {e}")
            return False

    def delete_fazenda(self, id_fazenda: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from fazenda where id_fazenda = :id_fazenda"), {"id_fazenda": id_fazenda})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting fazenda {id_fazenda}: {e}")
            return False

    # ------------------------------------------------------------------
    # Talhao
    # ------------------------------------------------------------------
    def create_talhao(
        self, id_fazenda: int, id_safra: int, nome: str, area_hectares: Decimal, conn=None
    ) -> TalhaoModel | None:
        sql = text(
            """
            insert into talhao (id_fazenda, id_safra, nome, area_hectares)
            values (:id_fazenda, :id_safra, :nome, :area_hectares)
            returning id_talhao
            """
        )
        try:
            with self._connection(conn) as c:
                id_talhao = c.execute(
                    sql,
                    {"id_fazenda": id_fazenda, "id_safra": id_safra, "nome": nome, "area_hectares": area_hectares},
                ).scalar_one()
                return TalhaoModel(
                    id_talhao=id_talhao,
                    id_fazenda=id_fazenda,
                    id_safra=id_safra,
                    nome=nome,
                    area_hectares=area_hectares,
                )
        except Exception as e:
            self.logger.error(f"Error creating talhao: {e}")
            return None

    def get_talhao_by_id(self, id_talhao: int) -> TalhaoModel | None:
        sql = text(
            "select id_talhao, id_fazenda, id_safra, nome, area_hectares from talhao where id_talhao = :id_talhao"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_talhao": id_talhao}).fetchone()
                return TalhaoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching talhao {id_talhao}: {e}")
            return None

    def list_talhoes(self, filters: dict | None = None) -> list[TalhaoModel]:
        where_sql, params = self._where_from_filters(
            filters, {"id_talhao", "id_fazenda", "id_safra", "nome", "area_hectares"}
        )
        sql = text(f"select id_talhao, id_fazenda, id_safra, nome, area_hectares from talhao {where_sql} order by id_talhao")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [TalhaoModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing talhoes: {e}")
            return []

    def update_talhao(
        self, id_talhao: int, nome: str | None = None, area_hectares: Decimal | None = None, conn=None
    ) -> bool:
        sql = text(
            """
            update talhao
            set nome = coalesce(:nome, nome),
                area_hectares = coalesce(:area_hectares, area_hectares)
            where id_talhao = :id_talhao
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"nome": nome, "area_hectares": area_hectares, "id_talhao": id_talhao})
            return True
        except Exception as e:
            self.logger.error(f"Error updating talhao {id_talhao}: {e}")
            return False

    def delete_talhao(self, id_talhao: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from talhao where id_talhao = :id_talhao"), {"id_talhao": id_talhao})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting talhao {id_talhao}: {e}")
            return False

    # ------------------------------------------------------------------
    # Solo (1:1 com Talhao)
    # ------------------------------------------------------------------
    def create_solo(
        self,
        id_talhao: int,
        tipo_solo: str | None = None,
        textura: str | None = None,
        profundidade_cm: Decimal | None = None,
        conn=None,
    ) -> SoloModel | None:
        sql = text(
            """
            insert into solo (id_talhao, tipo_solo, textura, profundidade_cm)
            values (:id_talhao, :tipo_solo, :textura, :profundidade_cm)
            returning id_solo
            """
        )
        try:
            with self._connection(conn) as c:
                id_solo = c.execute(
                    sql,
                    {
                        "id_talhao": id_talhao,
                        "tipo_solo": tipo_solo,
                        "textura": textura,
                        "profundidade_cm": profundidade_cm,
                    },
                ).scalar_one()
                return SoloModel(
                    id_solo=id_solo,
                    id_talhao=id_talhao,
                    tipo_solo=tipo_solo,
                    textura=textura,
                    profundidade_cm=profundidade_cm,
                )
        except Exception as e:
            self.logger.error(f"Error creating solo: {e}")
            return None

    def get_solo_by_talhao(self, id_talhao: int) -> SoloModel | None:
        sql = text(
            "select id_solo, id_talhao, tipo_solo, textura, profundidade_cm from solo where id_talhao = :id_talhao"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_talhao": id_talhao}).fetchone()
                return SoloModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching solo for talhao {id_talhao}: {e}")
            return None

    def list_solos(self, filters: dict | None = None) -> list[SoloModel]:
        where_sql, params = self._where_from_filters(
            filters, {"id_solo", "id_talhao", "tipo_solo", "textura", "profundidade_cm"}
        )
        sql = text(f"select id_solo, id_talhao, tipo_solo, textura, profundidade_cm from solo {where_sql} order by id_solo")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [SoloModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing solos: {e}")
            return []

    def update_solo(
        self,
        id_solo: int,
        tipo_solo: str | None = None,
        textura: str | None = None,
        profundidade_cm: Decimal | None = None,
        conn=None,
    ) -> bool:
        sql = text(
            """
            update solo
            set tipo_solo = coalesce(:tipo_solo, tipo_solo),
                textura = coalesce(:textura, textura),
                profundidade_cm = coalesce(:profundidade_cm, profundidade_cm)
            where id_solo = :id_solo
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(
                    sql,
                    {"tipo_solo": tipo_solo, "textura": textura, "profundidade_cm": profundidade_cm, "id_solo": id_solo},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating solo {id_solo}: {e}")
            return False

    def delete_solo(self, id_solo: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from solo where id_solo = :id_solo"), {"id_solo": id_solo})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting solo {id_solo}: {e}")
            return False

    # ------------------------------------------------------------------
    # CondicaoClimatica
    # ------------------------------------------------------------------
    def create_condicao_climatica(
        self,
        id_talhao: int,
        dt_registro: datetime,
        temperatura_min: Decimal | None = None,
        temperatura_max: Decimal | None = None,
        umidade_relativa: Decimal | None = None,
        precipitacao_mm: Decimal | None = None,
        velocidade_vento: Decimal | None = None,
        direcao_vento: str | None = None,
        radiacao_solar: Decimal | None = None,
        conn=None,
    ) -> CondicaoClimaticaModel | None:
        sql = text(
            """
            insert into condicao_climatica (
                id_talhao, dt_registro, temperatura_min, temperatura_max, umidade_relativa,
                precipitacao_mm, velocidade_vento, direcao_vento, radiacao_solar
            ) values (
                :id_talhao, :dt_registro, :temperatura_min, :temperatura_max, :umidade_relativa,
                :precipitacao_mm, :velocidade_vento, :direcao_vento, :radiacao_solar
            ) returning id_condicao
            """
        )
        params = {
            "id_talhao": id_talhao,
            "dt_registro": dt_registro,
            "temperatura_min": temperatura_min,
            "temperatura_max": temperatura_max,
            "umidade_relativa": umidade_relativa,
            "precipitacao_mm": precipitacao_mm,
            "velocidade_vento": velocidade_vento,
            "direcao_vento": direcao_vento,
            "radiacao_solar": radiacao_solar,
        }
        try:
            with self._connection(conn) as c:
                id_condicao = c.execute(sql, params).scalar_one()
                return CondicaoClimaticaModel(id_condicao=id_condicao, **params)
        except Exception as e:
            self.logger.error(f"Error creating condicao climatica: {e}")
            return None

    def get_condicao_climatica_by_id(self, id_condicao: int) -> CondicaoClimaticaModel | None:
        sql = text(
            """
            select id_condicao, id_talhao, dt_registro, temperatura_min, temperatura_max, umidade_relativa,
                   precipitacao_mm, velocidade_vento, direcao_vento, radiacao_solar
            from condicao_climatica where id_condicao = :id_condicao
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_condicao": id_condicao}).fetchone()
                return CondicaoClimaticaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching condicao climatica {id_condicao}: {e}")
            return None

    def list_condicoes_climaticas(self, filters: dict | None = None) -> list[CondicaoClimaticaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_condicao", "id_talhao", "dt_registro"})
        sql = text(
            f"""
            select id_condicao, id_talhao, dt_registro, temperatura_min, temperatura_max, umidade_relativa,
                   precipitacao_mm, velocidade_vento, direcao_vento, radiacao_solar
            from condicao_climatica {where_sql} order by dt_registro desc
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [CondicaoClimaticaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing condicoes climaticas: {e}")
            return []

    def delete_condicao_climatica(self, id_condicao: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from condicao_climatica where id_condicao = :id_condicao"),
                    {"id_condicao": id_condicao},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting condicao climatica {id_condicao}: {e}")
            return False

    # ------------------------------------------------------------------
    # Cultura
    # ------------------------------------------------------------------
    def create_cultura(
        self,
        nome: str,
        nome_cientifico: str | None = None,
        variedade: str | None = None,
        ciclo_dias: int | None = None,
        tipo_cultura: str | None = None,
        conn=None,
    ) -> CulturaModel | None:
        sql = text(
            """
            insert into cultura (nome, nome_cientifico, variedade, ciclo_dias, tipo_cultura)
            values (:nome, :nome_cientifico, :variedade, :ciclo_dias, :tipo_cultura)
            returning id_cultura
            """
        )
        params = {
            "nome": nome,
            "nome_cientifico": nome_cientifico,
            "variedade": variedade,
            "ciclo_dias": ciclo_dias,
            "tipo_cultura": tipo_cultura,
        }
        try:
            with self._connection(conn) as c:
                id_cultura = c.execute(sql, params).scalar_one()
                return CulturaModel(id_cultura=id_cultura, **params)
        except Exception as e:
            self.logger.error(f"Error creating cultura: {e}")
            return None

    def get_cultura_by_id(self, id_cultura: int) -> CulturaModel | None:
        sql = text(
            "select id_cultura, nome, nome_cientifico, variedade, ciclo_dias, tipo_cultura "
            "from cultura where id_cultura = :id_cultura"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_cultura": id_cultura}).fetchone()
                return CulturaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching cultura {id_cultura}: {e}")
            return None

    def list_culturas(self, filters: dict | None = None) -> list[CulturaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_cultura", "nome", "tipo_cultura"})
        sql = text(
            f"select id_cultura, nome, nome_cientifico, variedade, ciclo_dias, tipo_cultura "
            f"from cultura {where_sql} order by nome"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [CulturaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing culturas: {e}")
            return []

    def update_cultura(
        self,
        id_cultura: int,
        nome: str | None = None,
        nome_cientifico: str | None = None,
        variedade: str | None = None,
        ciclo_dias: int | None = None,
        tipo_cultura: str | None = None,
        conn=None,
    ) -> bool:
        sql = text(
            """
            update cultura
            set nome = coalesce(:nome, nome),
                nome_cientifico = coalesce(:nome_cientifico, nome_cientifico),
                variedade = coalesce(:variedade, variedade),
                ciclo_dias = coalesce(:ciclo_dias, ciclo_dias),
                tipo_cultura = coalesce(:tipo_cultura, tipo_cultura)
            where id_cultura = :id_cultura
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(
                    sql,
                    {
                        "nome": nome,
                        "nome_cientifico": nome_cientifico,
                        "variedade": variedade,
                        "ciclo_dias": ciclo_dias,
                        "tipo_cultura": tipo_cultura,
                        "id_cultura": id_cultura,
                    },
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating cultura {id_cultura}: {e}")
            return False

    def delete_cultura(self, id_cultura: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from cultura where id_cultura = :id_cultura"), {"id_cultura": id_cultura})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting cultura {id_cultura}: {e}")
            return False

    # ------------------------------------------------------------------
    # Safra
    # ------------------------------------------------------------------
    def create_safra(
        self,
        nome: str,
        ano: int,
        status: StatusSafra,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
        conn=None,
    ) -> SafraModel | None:
        sql = text(
            """
            insert into safra (nome, ano, dt_inicio, dt_fim, status)
            values (:nome, :ano, :dt_inicio, :dt_fim, :status)
            returning id_safra
            """
        )
        params = {"nome": nome, "ano": ano, "dt_inicio": dt_inicio, "dt_fim": dt_fim, "status": status.value}
        try:
            with self._connection(conn) as c:
                id_safra = c.execute(sql, params).scalar_one()
                return SafraModel(id_safra=id_safra, nome=nome, ano=ano, dt_inicio=dt_inicio, dt_fim=dt_fim, status=status)
        except Exception as e:
            self.logger.error(f"Error creating safra: {e}")
            return None

    def get_safra_by_id(self, id_safra: int) -> SafraModel | None:
        sql = text("select id_safra, nome, ano, dt_inicio, dt_fim, status from safra where id_safra = :id_safra")
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_safra": id_safra}).fetchone()
                return SafraModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching safra {id_safra}: {e}")
            return None

    def list_safras(self, filters: dict | None = None) -> list[SafraModel]:
        where_sql, params = self._where_from_filters(filters, {"id_safra", "nome", "ano", "status"})
        sql = text(f"select id_safra, nome, ano, dt_inicio, dt_fim, status from safra {where_sql} order by ano desc")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [SafraModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing safras: {e}")
            return []

    def update_safra(
        self,
        id_safra: int,
        nome: str | None = None,
        ano: int | None = None,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
        conn=None,
    ) -> bool:
        sql = text(
            """
            update safra
            set nome = coalesce(:nome, nome),
                ano = coalesce(:ano, ano),
                dt_inicio = coalesce(:dt_inicio, dt_inicio),
                dt_fim = coalesce(:dt_fim, dt_fim)
            where id_safra = :id_safra
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"nome": nome, "ano": ano, "dt_inicio": dt_inicio, "dt_fim": dt_fim, "id_safra": id_safra})
            return True
        except Exception as e:
            self.logger.error(f"Error updating safra {id_safra}: {e}")
            return False

    def update_status_safra(self, id_safra: int, status: StatusSafra, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update safra set status = :status where id_safra = :id_safra"),
                    {"status": status.value, "id_safra": id_safra},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of safra {id_safra}: {e}")
            return False

    def delete_safra(self, id_safra: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from safra where id_safra = :id_safra"), {"id_safra": id_safra})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting safra {id_safra}: {e}")
            return False

    # ------------------------------------------------------------------
    # PlanejamentoSafra
    # ------------------------------------------------------------------
    def create_planejamento_safra(
        self,
        id_safra: int,
        id_talhao: int,
        id_cultura: int,
        status: StatusPlanejamentoSafra,
        meta_produtividade: Decimal | None = None,
        area_planejada: Decimal | None = None,
        dt_plantio_previsto: date | None = None,
        dt_colheita_previsto: date | None = None,
        conn=None,
    ) -> PlanejamentoSafraModel | None:
        sql = text(
            """
            insert into planejamento_safra (
                id_safra, id_talhao, id_cultura, meta_produtividade, area_planejada,
                dt_plantio_previsto, dt_colheita_previsto, status
            ) values (
                :id_safra, :id_talhao, :id_cultura, :meta_produtividade, :area_planejada,
                :dt_plantio_previsto, :dt_colheita_previsto, :status
            ) returning id_planejamento
            """
        )
        params = {
            "id_safra": id_safra,
            "id_talhao": id_talhao,
            "id_cultura": id_cultura,
            "meta_produtividade": meta_produtividade,
            "area_planejada": area_planejada,
            "dt_plantio_previsto": dt_plantio_previsto,
            "dt_colheita_previsto": dt_colheita_previsto,
            "status": status.value,
        }
        try:
            with self._connection(conn) as c:
                id_planejamento = c.execute(sql, params).scalar_one()
                return PlanejamentoSafraModel(id_planejamento=id_planejamento, **{**params, "status": status})
        except Exception as e:
            self.logger.error(f"Error creating planejamento_safra: {e}")
            return None

    def get_planejamento_safra_by_id(self, id_planejamento: int) -> PlanejamentoSafraModel | None:
        sql = text(
            """
            select id_planejamento, id_safra, id_talhao, id_cultura, meta_produtividade, area_planejada,
                   dt_plantio_previsto, dt_colheita_previsto, status
            from planejamento_safra where id_planejamento = :id_planejamento
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_planejamento": id_planejamento}).fetchone()
                return PlanejamentoSafraModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching planejamento_safra {id_planejamento}: {e}")
            return None

    def list_planejamentos_safra(self, filters: dict | None = None) -> list[PlanejamentoSafraModel]:
        where_sql, params = self._where_from_filters(
            filters, {"id_planejamento", "id_safra", "id_talhao", "id_cultura", "status"}
        )
        sql = text(
            f"""
            select id_planejamento, id_safra, id_talhao, id_cultura, meta_produtividade, area_planejada,
                   dt_plantio_previsto, dt_colheita_previsto, status
            from planejamento_safra {where_sql} order by id_planejamento
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [PlanejamentoSafraModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing planejamentos_safra: {e}")
            return []

    def update_planejamento_safra(
        self,
        id_planejamento: int,
        meta_produtividade: Decimal | None = None,
        area_planejada: Decimal | None = None,
        dt_plantio_previsto: date | None = None,
        dt_colheita_previsto: date | None = None,
        conn=None,
    ) -> bool:
        sql = text(
            """
            update planejamento_safra
            set meta_produtividade = coalesce(:meta_produtividade, meta_produtividade),
                area_planejada = coalesce(:area_planejada, area_planejada),
                dt_plantio_previsto = coalesce(:dt_plantio_previsto, dt_plantio_previsto),
                dt_colheita_previsto = coalesce(:dt_colheita_previsto, dt_colheita_previsto)
            where id_planejamento = :id_planejamento
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(
                    sql,
                    {
                        "meta_produtividade": meta_produtividade,
                        "area_planejada": area_planejada,
                        "dt_plantio_previsto": dt_plantio_previsto,
                        "dt_colheita_previsto": dt_colheita_previsto,
                        "id_planejamento": id_planejamento,
                    },
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating planejamento_safra {id_planejamento}: {e}")
            return False

    def update_status_planejamento_safra(
        self, id_planejamento: int, status: StatusPlanejamentoSafra, conn=None
    ) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update planejamento_safra set status = :status where id_planejamento = :id_planejamento"),
                    {"status": status.value, "id_planejamento": id_planejamento},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of planejamento_safra {id_planejamento}: {e}")
            return False

    def delete_planejamento_safra(self, id_planejamento: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from planejamento_safra where id_planejamento = :id_planejamento"),
                    {"id_planejamento": id_planejamento},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting planejamento_safra {id_planejamento}: {e}")
            return False

    # ------------------------------------------------------------------
    # AnaliseSolo
    # ------------------------------------------------------------------
    def create_analise_solo(
        self,
        id_solo: int,
        id_safra: int,
        id_funcionario: int,
        dt_coleta: date | None = None,
        dt_resultado: date | None = None,
        ph: Decimal | None = None,
        materia_organica: Decimal | None = None,
        fosforo: Decimal | None = None,
        potassio: Decimal | None = None,
        calcio: Decimal | None = None,
        magnesio: Decimal | None = None,
        saturacao_bases: Decimal | None = None,
        observacao: str | None = None,
        conn=None,
    ) -> AnaliseSoloModel | None:
        sql = text(
            """
            insert into analise_solo (
                id_solo, id_safra, id_funcionario, dt_coleta, dt_resultado, ph, materia_organica,
                fosforo, potassio, calcio, magnesio, saturacao_bases, observacao
            ) values (
                :id_solo, :id_safra, :id_funcionario, :dt_coleta, :dt_resultado, :ph, :materia_organica,
                :fosforo, :potassio, :calcio, :magnesio, :saturacao_bases, :observacao
            ) returning id_analise
            """
        )
        params = {
            "id_solo": id_solo,
            "id_safra": id_safra,
            "id_funcionario": id_funcionario,
            "dt_coleta": dt_coleta,
            "dt_resultado": dt_resultado,
            "ph": ph,
            "materia_organica": materia_organica,
            "fosforo": fosforo,
            "potassio": potassio,
            "calcio": calcio,
            "magnesio": magnesio,
            "saturacao_bases": saturacao_bases,
            "observacao": observacao,
        }
        try:
            with self._connection(conn) as c:
                id_analise = c.execute(sql, params).scalar_one()
                return AnaliseSoloModel(id_analise=id_analise, **params)
        except Exception as e:
            self.logger.error(f"Error creating analise_solo: {e}")
            return None

    def get_analise_solo_by_id(self, id_analise: int) -> AnaliseSoloModel | None:
        sql = text(
            """
            select id_analise, id_solo, id_safra, id_funcionario, dt_coleta, dt_resultado, ph, materia_organica,
                   fosforo, potassio, calcio, magnesio, saturacao_bases, observacao
            from analise_solo where id_analise = :id_analise
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_analise": id_analise}).fetchone()
                return AnaliseSoloModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching analise_solo {id_analise}: {e}")
            return None

    def list_analises_solo(self, filters: dict | None = None) -> list[AnaliseSoloModel]:
        where_sql, params = self._where_from_filters(filters, {"id_analise", "id_solo", "id_safra", "id_funcionario"})
        sql = text(
            f"""
            select id_analise, id_solo, id_safra, id_funcionario, dt_coleta, dt_resultado, ph, materia_organica,
                   fosforo, potassio, calcio, magnesio, saturacao_bases, observacao
            from analise_solo {where_sql} order by id_analise
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [AnaliseSoloModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing analises_solo: {e}")
            return []

    def delete_analise_solo(self, id_analise: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from analise_solo where id_analise = :id_analise"), {"id_analise": id_analise})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting analise_solo {id_analise}: {e}")
            return False

    # ------------------------------------------------------------------
    # MonitoramentoSafra
    # ------------------------------------------------------------------
    def create_monitoramento_safra(
        self,
        id_safra: int,
        id_talhao: int,
        id_funcionario: int,
        dt_monitoramento: datetime,
        estagio_fenologico: str | None = None,
        observacao: str | None = None,
        conn=None,
    ) -> MonitoramentoSafraModel | None:
        sql = text(
            """
            insert into monitoramento_safra (
                id_safra, id_talhao, id_funcionario, dt_monitoramento, estagio_fenologico, observacao
            ) values (
                :id_safra, :id_talhao, :id_funcionario, :dt_monitoramento, :estagio_fenologico, :observacao
            ) returning id_monitoramento
            """
        )
        params = {
            "id_safra": id_safra,
            "id_talhao": id_talhao,
            "id_funcionario": id_funcionario,
            "dt_monitoramento": dt_monitoramento,
            "estagio_fenologico": estagio_fenologico,
            "observacao": observacao,
        }
        try:
            with self._connection(conn) as c:
                id_monitoramento = c.execute(sql, params).scalar_one()
                return MonitoramentoSafraModel(id_monitoramento=id_monitoramento, **params)
        except Exception as e:
            self.logger.error(f"Error creating monitoramento_safra: {e}")
            return None

    def get_monitoramento_safra_by_id(self, id_monitoramento: int) -> MonitoramentoSafraModel | None:
        sql = text(
            """
            select id_monitoramento, id_safra, id_talhao, id_funcionario, dt_monitoramento,
                   estagio_fenologico, observacao
            from monitoramento_safra where id_monitoramento = :id_monitoramento
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_monitoramento": id_monitoramento}).fetchone()
                return MonitoramentoSafraModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching monitoramento_safra {id_monitoramento}: {e}")
            return None

    def list_monitoramentos_safra(self, filters: dict | None = None) -> list[MonitoramentoSafraModel]:
        where_sql, params = self._where_from_filters(filters, {"id_monitoramento", "id_safra", "id_talhao", "id_funcionario"})
        sql = text(
            f"""
            select id_monitoramento, id_safra, id_talhao, id_funcionario, dt_monitoramento,
                   estagio_fenologico, observacao
            from monitoramento_safra {where_sql} order by dt_monitoramento desc
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [MonitoramentoSafraModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing monitoramentos_safra: {e}")
            return []

    def delete_monitoramento_safra(self, id_monitoramento: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from monitoramento_safra where id_monitoramento = :id_monitoramento"),
                    {"id_monitoramento": id_monitoramento},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting monitoramento_safra {id_monitoramento}: {e}")
            return False

    # ------------------------------------------------------------------
    # ParametroMonitoramento
    # ------------------------------------------------------------------
    def create_parametro_monitoramento(
        self,
        id_monitoramento: int,
        nome_parametro: str,
        valor: Decimal | None = None,
        unidade: str | None = None,
        conn=None,
    ) -> ParametroMonitoramentoModel | None:
        sql = text(
            """
            insert into parametro_monitoramento (id_monitoramento, nome_parametro, valor, unidade)
            values (:id_monitoramento, :nome_parametro, :valor, :unidade)
            returning id_parametro
            """
        )
        params = {
            "id_monitoramento": id_monitoramento,
            "nome_parametro": nome_parametro,
            "valor": valor,
            "unidade": unidade,
        }
        try:
            with self._connection(conn) as c:
                id_parametro = c.execute(sql, params).scalar_one()
                return ParametroMonitoramentoModel(id_parametro=id_parametro, **params)
        except Exception as e:
            self.logger.error(f"Error creating parametro_monitoramento: {e}")
            return None

    def list_parametros_por_monitoramento(self, id_monitoramento: int) -> list[ParametroMonitoramentoModel]:
        sql = text(
            """
            select id_parametro, id_monitoramento, nome_parametro, valor, unidade
            from parametro_monitoramento where id_monitoramento = :id_monitoramento
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [
                    ParametroMonitoramentoModel(**row._mapping)
                    for row in conn.execute(sql, {"id_monitoramento": id_monitoramento})
                ]
        except Exception as e:
            self.logger.error(f"Error listing parametros for monitoramento {id_monitoramento}: {e}")
            return []

    def delete_parametro_monitoramento(self, id_parametro: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from parametro_monitoramento where id_parametro = :id_parametro"),
                    {"id_parametro": id_parametro},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting parametro_monitoramento {id_parametro}: {e}")
            return False

    # ------------------------------------------------------------------
    # OrdemProducao
    # ------------------------------------------------------------------
    def create_ordem_producao(
        self, id_safra: int, status: StatusOrdemProducao, data_abertura: date | None = None, conn=None
    ) -> OrdemProducaoModel | None:
        sql = text(
            """
            insert into ordem_producao (id_safra, data_abertura, status)
            values (:id_safra, :data_abertura, :status)
            returning id_ordem
            """
        )
        try:
            with self._connection(conn) as c:
                id_ordem = c.execute(
                    sql, {"id_safra": id_safra, "data_abertura": data_abertura, "status": status.value}
                ).scalar_one()
                return OrdemProducaoModel(id_ordem=id_ordem, id_safra=id_safra, data_abertura=data_abertura, status=status)
        except Exception as e:
            self.logger.error(f"Error creating ordem_producao: {e}")
            return None

    def get_ordem_producao_by_id(self, id_ordem: int) -> OrdemProducaoModel | None:
        sql = text("select id_ordem, id_safra, data_abertura, status from ordem_producao where id_ordem = :id_ordem")
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_ordem": id_ordem}).fetchone()
                return OrdemProducaoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching ordem_producao {id_ordem}: {e}")
            return None

    def list_ordens_producao(self, filters: dict | None = None) -> list[OrdemProducaoModel]:
        where_sql, params = self._where_from_filters(filters, {"id_ordem", "id_safra", "status"})
        sql = text(f"select id_ordem, id_safra, data_abertura, status from ordem_producao {where_sql} order by id_ordem")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [OrdemProducaoModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing ordens_producao: {e}")
            return []

    def update_status_ordem_producao(self, id_ordem: int, status: StatusOrdemProducao, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update ordem_producao set status = :status where id_ordem = :id_ordem"),
                    {"status": status.value, "id_ordem": id_ordem},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of ordem_producao {id_ordem}: {e}")
            return False

    def delete_ordem_producao(self, id_ordem: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from ordem_producao where id_ordem = :id_ordem"), {"id_ordem": id_ordem})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting ordem_producao {id_ordem}: {e}")
            return False

    # ------------------------------------------------------------------
    # Plantio
    # ------------------------------------------------------------------
    def create_plantio(
        self,
        id_ordem: int,
        id_talhao: int,
        id_produto: int,
        id_cultura: int,
        id_planejamento: int,
        status: StatusPlantio,
        dt_plantio: date | None = None,
        conn=None,
    ) -> PlantioModel | None:
        sql = text(
            """
            insert into plantio (id_ordem, id_talhao, id_produto, id_cultura, id_planejamento, dt_plantio, status)
            values (:id_ordem, :id_talhao, :id_produto, :id_cultura, :id_planejamento, :dt_plantio, :status)
            returning id_plantio
            """
        )
        params = {
            "id_ordem": id_ordem,
            "id_talhao": id_talhao,
            "id_produto": id_produto,
            "id_cultura": id_cultura,
            "id_planejamento": id_planejamento,
            "dt_plantio": dt_plantio,
            "status": status.value,
        }
        try:
            with self._connection(conn) as c:
                id_plantio = c.execute(sql, params).scalar_one()
                return PlantioModel(id_plantio=id_plantio, **{**params, "status": status})
        except Exception as e:
            self.logger.error(f"Error creating plantio: {e}")
            return None

    def get_plantio_by_id(self, id_plantio: int) -> PlantioModel | None:
        sql = text(
            """
            select id_plantio, id_ordem, id_talhao, id_produto, id_cultura, id_planejamento, dt_plantio, status
            from plantio where id_plantio = :id_plantio
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_plantio": id_plantio}).fetchone()
                return PlantioModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching plantio {id_plantio}: {e}")
            return None

    def list_plantios(self, filters: dict | None = None) -> list[PlantioModel]:
        where_sql, params = self._where_from_filters(
            filters, {"id_plantio", "id_ordem", "id_talhao", "id_cultura", "id_planejamento", "status"}
        )
        sql = text(
            f"""
            select id_plantio, id_ordem, id_talhao, id_produto, id_cultura, id_planejamento, dt_plantio, status
            from plantio {where_sql} order by id_plantio
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [PlantioModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing plantios: {e}")
            return []

    def update_status_plantio(self, id_plantio: int, status: StatusPlantio, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update plantio set status = :status where id_plantio = :id_plantio"),
                    {"status": status.value, "id_plantio": id_plantio},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of plantio {id_plantio}: {e}")
            return False

    def delete_plantio(self, id_plantio: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from plantio where id_plantio = :id_plantio"), {"id_plantio": id_plantio})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting plantio {id_plantio}: {e}")
            return False

    # ------------------------------------------------------------------
    # OperacaoAgricola
    # ------------------------------------------------------------------
    def create_operacao_agricola(
        self,
        id_plantio: int,
        id_funcionario: int,
        status: StatusOperacaoAgricola,
        tipo_operacao: str | None = None,
        descricao: str | None = None,
        dt_inicio: datetime | None = None,
        dt_fim: datetime | None = None,
        conn=None,
    ) -> OperacaoAgricolaModel | None:
        sql = text(
            """
            insert into operacao_agricola (
                id_plantio, id_funcionario, tipo_operacao, descricao, dt_inicio, dt_fim, status
            ) values (
                :id_plantio, :id_funcionario, :tipo_operacao, :descricao, :dt_inicio, :dt_fim, :status
            ) returning id_operacao
            """
        )
        params = {
            "id_plantio": id_plantio,
            "id_funcionario": id_funcionario,
            "tipo_operacao": tipo_operacao,
            "descricao": descricao,
            "dt_inicio": dt_inicio,
            "dt_fim": dt_fim,
            "status": status.value,
        }
        try:
            with self._connection(conn) as c:
                id_operacao = c.execute(sql, params).scalar_one()
                return OperacaoAgricolaModel(id_operacao=id_operacao, **{**params, "status": status})
        except Exception as e:
            self.logger.error(f"Error creating operacao_agricola: {e}")
            return None

    def get_operacao_agricola_by_id(self, id_operacao: int) -> OperacaoAgricolaModel | None:
        sql = text(
            """
            select id_operacao, id_plantio, id_funcionario, tipo_operacao, descricao, dt_inicio, dt_fim, status
            from operacao_agricola where id_operacao = :id_operacao
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_operacao": id_operacao}).fetchone()
                return OperacaoAgricolaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching operacao_agricola {id_operacao}: {e}")
            return None

    def list_operacoes_agricolas(self, filters: dict | None = None) -> list[OperacaoAgricolaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_operacao", "id_plantio", "id_funcionario", "status"})
        sql = text(
            f"""
            select id_operacao, id_plantio, id_funcionario, tipo_operacao, descricao, dt_inicio, dt_fim, status
            from operacao_agricola {where_sql} order by id_operacao
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [OperacaoAgricolaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing operacoes_agricolas: {e}")
            return []

    def update_status_operacao_agricola(self, id_operacao: int, status: StatusOperacaoAgricola, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update operacao_agricola set status = :status where id_operacao = :id_operacao"),
                    {"status": status.value, "id_operacao": id_operacao},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of operacao_agricola {id_operacao}: {e}")
            return False

    def delete_operacao_agricola(self, id_operacao: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from operacao_agricola where id_operacao = :id_operacao"), {"id_operacao": id_operacao}
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting operacao_agricola {id_operacao}: {e}")
            return False

    # ------------------------------------------------------------------
    # AtividadeAgricola
    # ------------------------------------------------------------------
    def create_atividade_agricola(
        self,
        id_operacao: int,
        status: StatusAtividadeAgricola,
        descricao: str | None = None,
        dt_inicio: datetime | None = None,
        dt_fim: datetime | None = None,
        conn=None,
    ) -> AtividadeAgricolaModel | None:
        sql = text(
            """
            insert into atividade_agricola (id_operacao, descricao, dt_inicio, dt_fim, status)
            values (:id_operacao, :descricao, :dt_inicio, :dt_fim, :status)
            returning id_atividade
            """
        )
        params = {
            "id_operacao": id_operacao,
            "descricao": descricao,
            "dt_inicio": dt_inicio,
            "dt_fim": dt_fim,
            "status": status.value,
        }
        try:
            with self._connection(conn) as c:
                id_atividade = c.execute(sql, params).scalar_one()
                return AtividadeAgricolaModel(id_atividade=id_atividade, **{**params, "status": status})
        except Exception as e:
            self.logger.error(f"Error creating atividade_agricola: {e}")
            return None

    def get_atividade_agricola_by_id(self, id_atividade: int) -> AtividadeAgricolaModel | None:
        sql = text(
            """
            select id_atividade, id_operacao, descricao, dt_inicio, dt_fim, status
            from atividade_agricola where id_atividade = :id_atividade
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_atividade": id_atividade}).fetchone()
                return AtividadeAgricolaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching atividade_agricola {id_atividade}: {e}")
            return None

    def list_atividades_agricolas(self, filters: dict | None = None) -> list[AtividadeAgricolaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_atividade", "id_operacao", "status"})
        sql = text(
            f"""
            select id_atividade, id_operacao, descricao, dt_inicio, dt_fim, status
            from atividade_agricola {where_sql} order by id_atividade
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [AtividadeAgricolaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing atividades_agricolas: {e}")
            return []

    def update_status_atividade_agricola(self, id_atividade: int, status: StatusAtividadeAgricola, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update atividade_agricola set status = :status where id_atividade = :id_atividade"),
                    {"status": status.value, "id_atividade": id_atividade},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of atividade_agricola {id_atividade}: {e}")
            return False

    def delete_atividade_agricola(self, id_atividade: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from atividade_agricola where id_atividade = :id_atividade"),
                    {"id_atividade": id_atividade},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting atividade_agricola {id_atividade}: {e}")
            return False

    # ------------------------------------------------------------------
    # FuncionarioAtividade (tabela associativa, PK composta)
    # ------------------------------------------------------------------
    def link_funcionario_atividade(self, id_funcionario: int, id_atividade: int, conn=None) -> bool:
        sql = text(
            """
            insert into funcionario_atividade (id_funcionario, id_atividade)
            values (:id_funcionario, :id_atividade)
            on conflict do nothing
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"id_funcionario": id_funcionario, "id_atividade": id_atividade})
            return True
        except Exception as e:
            self.logger.error(f"Error linking funcionario {id_funcionario} to atividade {id_atividade}: {e}")
            return False

    def unlink_funcionario_atividade(self, id_funcionario: int, id_atividade: int, conn=None) -> bool:
        sql = text(
            "delete from funcionario_atividade where id_funcionario = :id_funcionario and id_atividade = :id_atividade"
        )
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"id_funcionario": id_funcionario, "id_atividade": id_atividade})
            return True
        except Exception as e:
            self.logger.error(f"Error unlinking funcionario {id_funcionario} from atividade {id_atividade}: {e}")
            return False

    def list_funcionarios_por_atividade(self, id_atividade: int) -> list[FuncionarioAtividadeModel]:
        sql = text("select id_funcionario, id_atividade from funcionario_atividade where id_atividade = :id_atividade")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [
                    FuncionarioAtividadeModel(**row._mapping)
                    for row in conn.execute(sql, {"id_atividade": id_atividade})
                ]
        except Exception as e:
            self.logger.error(f"Error listing funcionarios for atividade {id_atividade}: {e}")
            return []

    def list_atividades_por_funcionario(self, id_funcionario: int) -> list[FuncionarioAtividadeModel]:
        sql = text("select id_funcionario, id_atividade from funcionario_atividade where id_funcionario = :id_funcionario")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [
                    FuncionarioAtividadeModel(**row._mapping)
                    for row in conn.execute(sql, {"id_funcionario": id_funcionario})
                ]
        except Exception as e:
            self.logger.error(f"Error listing atividades for funcionario {id_funcionario}: {e}")
            return []

    # ------------------------------------------------------------------
    # Adubacao (detalhe 1:1 de AtividadeAgricola, PK = FK)
    # ------------------------------------------------------------------
    def upsert_adubacao(
        self,
        id_atividade: int,
        id_insumo: int,
        tipo_adubacao: str | None = None,
        dose_hectare: Decimal | None = None,
        metodo_aplicacao: str | None = None,
        conn=None,
    ) -> AdubacaoModel | None:
        sql = text(
            """
            insert into adubacao (id_atividade, id_insumo, tipo_adubacao, dose_hectare, metodo_aplicacao)
            values (:id_atividade, :id_insumo, :tipo_adubacao, :dose_hectare, :metodo_aplicacao)
            on conflict (id_atividade) do update
            set id_insumo = excluded.id_insumo,
                tipo_adubacao = excluded.tipo_adubacao,
                dose_hectare = excluded.dose_hectare,
                metodo_aplicacao = excluded.metodo_aplicacao
            """
        )
        params = {
            "id_atividade": id_atividade,
            "id_insumo": id_insumo,
            "tipo_adubacao": tipo_adubacao,
            "dose_hectare": dose_hectare,
            "metodo_aplicacao": metodo_aplicacao,
        }
        try:
            with self._connection(conn) as c:
                c.execute(sql, params)
                return AdubacaoModel(**params)
        except Exception as e:
            self.logger.error(f"Error upserting adubacao for atividade {id_atividade}: {e}")
            return None

    def get_adubacao_by_atividade(self, id_atividade: int) -> AdubacaoModel | None:
        sql = text(
            "select id_atividade, id_insumo, tipo_adubacao, dose_hectare, metodo_aplicacao "
            "from adubacao where id_atividade = :id_atividade"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_atividade": id_atividade}).fetchone()
                return AdubacaoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching adubacao for atividade {id_atividade}: {e}")
            return None

    def delete_adubacao(self, id_atividade: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from adubacao where id_atividade = :id_atividade"), {"id_atividade": id_atividade})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting adubacao for atividade {id_atividade}: {e}")
            return False

    # ------------------------------------------------------------------
    # Irrigacao (detalhe 1:1 de AtividadeAgricola, PK = FK)
    # ------------------------------------------------------------------
    def upsert_irrigacao(
        self,
        id_atividade: int,
        lamina_agua: Decimal | None = None,
        metodo_irrigacao: str | None = None,
        duracao_horas: Decimal | None = None,
        conn=None,
    ) -> IrrigacaoModel | None:
        sql = text(
            """
            insert into irrigacao (id_atividade, lamina_agua, metodo_irrigacao, duracao_horas)
            values (:id_atividade, :lamina_agua, :metodo_irrigacao, :duracao_horas)
            on conflict (id_atividade) do update
            set lamina_agua = excluded.lamina_agua,
                metodo_irrigacao = excluded.metodo_irrigacao,
                duracao_horas = excluded.duracao_horas
            """
        )
        params = {
            "id_atividade": id_atividade,
            "lamina_agua": lamina_agua,
            "metodo_irrigacao": metodo_irrigacao,
            "duracao_horas": duracao_horas,
        }
        try:
            with self._connection(conn) as c:
                c.execute(sql, params)
                return IrrigacaoModel(**params)
        except Exception as e:
            self.logger.error(f"Error upserting irrigacao for atividade {id_atividade}: {e}")
            return None

    def get_irrigacao_by_atividade(self, id_atividade: int) -> IrrigacaoModel | None:
        sql = text(
            "select id_atividade, lamina_agua, metodo_irrigacao, duracao_horas "
            "from irrigacao where id_atividade = :id_atividade"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_atividade": id_atividade}).fetchone()
                return IrrigacaoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching irrigacao for atividade {id_atividade}: {e}")
            return None

    def delete_irrigacao(self, id_atividade: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from irrigacao where id_atividade = :id_atividade"), {"id_atividade": id_atividade})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting irrigacao for atividade {id_atividade}: {e}")
            return False

    # ------------------------------------------------------------------
    # Pulverizacao (detalhe 1:1 de AtividadeAgricola, PK = FK)
    # ------------------------------------------------------------------
    def upsert_pulverizacao(
        self,
        id_atividade: int,
        id_insumo: int,
        volume_calda: Decimal | None = None,
        vazao: Decimal | None = None,
        conn=None,
    ) -> PulverizacaoModel | None:
        sql = text(
            """
            insert into pulverizacao (id_atividade, id_insumo, volume_calda, vazao)
            values (:id_atividade, :id_insumo, :volume_calda, :vazao)
            on conflict (id_atividade) do update
            set id_insumo = excluded.id_insumo,
                volume_calda = excluded.volume_calda,
                vazao = excluded.vazao
            """
        )
        params = {"id_atividade": id_atividade, "id_insumo": id_insumo, "volume_calda": volume_calda, "vazao": vazao}
        try:
            with self._connection(conn) as c:
                c.execute(sql, params)
                return PulverizacaoModel(**params)
        except Exception as e:
            self.logger.error(f"Error upserting pulverizacao for atividade {id_atividade}: {e}")
            return None

    def get_pulverizacao_by_atividade(self, id_atividade: int) -> PulverizacaoModel | None:
        sql = text(
            "select id_atividade, id_insumo, volume_calda, vazao from pulverizacao where id_atividade = :id_atividade"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_atividade": id_atividade}).fetchone()
                return PulverizacaoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching pulverizacao for atividade {id_atividade}: {e}")
            return None

    def delete_pulverizacao(self, id_atividade: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from pulverizacao where id_atividade = :id_atividade"), {"id_atividade": id_atividade}
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting pulverizacao for atividade {id_atividade}: {e}")
            return False

    # ------------------------------------------------------------------
    # Colheita
    # ------------------------------------------------------------------
    def create_colheita(
        self,
        id_plantio: int,
        status: StatusColheita,
        quantidade_colhida: Decimal | None = None,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
        conn=None,
    ) -> ColheitaModel | None:
        sql = text(
            """
            insert into colheita (id_plantio, quantidade_colhida, dt_inicio, dt_fim, status)
            values (:id_plantio, :quantidade_colhida, :dt_inicio, :dt_fim, :status)
            returning id_colheita
            """
        )
        params = {
            "id_plantio": id_plantio,
            "quantidade_colhida": quantidade_colhida,
            "dt_inicio": dt_inicio,
            "dt_fim": dt_fim,
            "status": status.value,
        }
        try:
            with self._connection(conn) as c:
                id_colheita = c.execute(sql, params).scalar_one()
                return ColheitaModel(id_colheita=id_colheita, **{**params, "status": status})
        except Exception as e:
            self.logger.error(f"Error creating colheita: {e}")
            return None

    def get_colheita_by_id(self, id_colheita: int) -> ColheitaModel | None:
        sql = text(
            """
            select id_colheita, id_plantio, quantidade_colhida, dt_inicio, dt_fim, status
            from colheita where id_colheita = :id_colheita
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_colheita": id_colheita}).fetchone()
                return ColheitaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching colheita {id_colheita}: {e}")
            return None

    def list_colheitas(self, filters: dict | None = None) -> list[ColheitaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_colheita", "id_plantio", "status"})
        sql = text(
            f"""
            select id_colheita, id_plantio, quantidade_colhida, dt_inicio, dt_fim, status
            from colheita {where_sql} order by id_colheita
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [ColheitaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing colheitas: {e}")
            return []

    def update_status_colheita(self, id_colheita: int, status: StatusColheita, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update colheita set status = :status where id_colheita = :id_colheita"),
                    {"status": status.value, "id_colheita": id_colheita},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of colheita {id_colheita}: {e}")
            return False

    def delete_colheita(self, id_colheita: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from colheita where id_colheita = :id_colheita"), {"id_colheita": id_colheita})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting colheita {id_colheita}: {e}")
            return False
