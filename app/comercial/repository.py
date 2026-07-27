from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.comercial.enum import StatusCliente, UnitSymbol
from app.core.enum import StatusCertificacao
from app.comercial.models import (
    CategoriaProdutoModel,
    CentroCustoOption,
    CertificacaoFazendaModel,
    CertificacaoModel,
    ClienteModel,
    ClienteOption,
    CotacaoGraoModel,
    GraoModel,
    InsumoModel,
    ItemVendaModel,
    LoteInfo,
    LoteOption,
    ProdutoComercialModel,
    ProdutoModel,
    ProdutoOption,
    UnidadeMedidaModel,
    VendaModel,
)


class ComercialRepository:
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
    # CategoriaProduto
    # ------------------------------------------------------------------
    def create_categoria_produto(self, nome: str, conn=None) -> CategoriaProdutoModel | None:
        sql = text("insert into categoria_produto (nome) values (:nome) returning id_categoria")
        try:
            with self._connection(conn) as c:
                id_categoria = c.execute(sql, {"nome": nome}).scalar_one()
                return CategoriaProdutoModel(id_categoria=id_categoria, nome=nome)
        except Exception as e:
            self.logger.error(f"Error creating categoria_produto: {e}")
            return None

    def get_categoria_produto_by_id(self, id_categoria: int) -> CategoriaProdutoModel | None:
        sql = text("select id_categoria, nome from categoria_produto where id_categoria = :id_categoria")
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_categoria": id_categoria}).fetchone()
                return CategoriaProdutoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching categoria_produto {id_categoria}: {e}")
            return None

    def list_categorias_produto(self, filters: dict | None = None) -> list[CategoriaProdutoModel]:
        where_sql, params = self._where_from_filters(filters, {"id_categoria", "nome"})
        sql = text(f"select id_categoria, nome from categoria_produto {where_sql} order by nome")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [CategoriaProdutoModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing categorias_produto: {e}")
            return []

    def update_categoria_produto(self, id_categoria: int, nome: str | None = None, conn=None) -> bool:
        sql = text("update categoria_produto set nome = coalesce(:nome, nome) where id_categoria = :id_categoria")
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"nome": nome, "id_categoria": id_categoria})
            return True
        except Exception as e:
            self.logger.error(f"Error updating categoria_produto {id_categoria}: {e}")
            return False

    def delete_categoria_produto(self, id_categoria: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from categoria_produto where id_categoria = :id_categoria"),
                    {"id_categoria": id_categoria},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting categoria_produto {id_categoria}: {e}")
            return False

    # ------------------------------------------------------------------
    # UnidadeMedida
    # ------------------------------------------------------------------
    def create_unidade_medida(self, sigla: UnitSymbol, descricao: str, conn=None) -> UnidadeMedidaModel | None:
        sql = text(
            "insert into unidade_medida (sigla, descricao) values (:sigla, :descricao) returning id_unidade"
        )
        try:
            with self._connection(conn) as c:
                id_unidade = c.execute(sql, {"sigla": sigla.value, "descricao": descricao}).scalar_one()
                return UnidadeMedidaModel(id_unidade=id_unidade, sigla=sigla, descricao=descricao)
        except Exception as e:
            self.logger.error(f"Error creating unidade_medida: {e}")
            return None

    def get_unidade_medida_by_id(self, id_unidade: int) -> UnidadeMedidaModel | None:
        sql = text("select id_unidade, sigla, descricao from unidade_medida where id_unidade = :id_unidade")
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_unidade": id_unidade}).fetchone()
                return UnidadeMedidaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching unidade_medida {id_unidade}: {e}")
            return None

    def list_unidades_medida(self, filters: dict | None = None) -> list[UnidadeMedidaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_unidade", "sigla"})
        sql = text(f"select id_unidade, sigla, descricao from unidade_medida {where_sql} order by sigla")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [UnidadeMedidaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing unidades_medida: {e}")
            return []

    def update_unidade_medida(self, id_unidade: int, descricao: str | None = None, conn=None) -> bool:
        sql = text(
            "update unidade_medida set descricao = coalesce(:descricao, descricao) where id_unidade = :id_unidade"
        )
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"descricao": descricao, "id_unidade": id_unidade})
            return True
        except Exception as e:
            self.logger.error(f"Error updating unidade_medida {id_unidade}: {e}")
            return False

    def delete_unidade_medida(self, id_unidade: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from unidade_medida where id_unidade = :id_unidade"), {"id_unidade": id_unidade})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting unidade_medida {id_unidade}: {e}")
            return False

    # ------------------------------------------------------------------
    # Produto
    # ------------------------------------------------------------------
    def create_produto(
        self,
        id_categoria: int,
        id_unidade: int,
        nome: str,
        tipo: str | None = None,
        preco: Decimal | None = None,
        conn=None,
    ) -> ProdutoModel | None:
        sql = text(
            """
            insert into produto (id_categoria, id_unidade, nome, tipo, preco)
            values (:id_categoria, :id_unidade, :nome, :tipo, :preco)
            returning id_produto
            """
        )
        params = {"id_categoria": id_categoria, "id_unidade": id_unidade, "nome": nome, "tipo": tipo, "preco": preco}
        try:
            with self._connection(conn) as c:
                id_produto = c.execute(sql, params).scalar_one()
                return ProdutoModel(id_produto=id_produto, **params)
        except Exception as e:
            self.logger.error(f"Error creating produto: {e}")
            return None

    def get_produto_by_id(self, id_produto: int) -> ProdutoModel | None:
        sql = text(
            "select id_produto, id_categoria, id_unidade, nome, tipo, preco from produto where id_produto = :id_produto"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_produto": id_produto}).fetchone()
                return ProdutoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching produto {id_produto}: {e}")
            return None

    def list_produtos(self, filters: dict | None = None) -> list[ProdutoModel]:
        where_sql, params = self._where_from_filters(filters, {"id_produto", "id_categoria", "id_unidade", "nome"})
        sql = text(
            f"select id_produto, id_categoria, id_unidade, nome, tipo, preco from produto {where_sql} order by nome"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [ProdutoModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing produtos: {e}")
            return []

    def update_produto(
        self,
        id_produto: int,
        nome: str | None = None,
        tipo: str | None = None,
        preco: Decimal | None = None,
        conn=None,
    ) -> bool:
        sql = text(
            """
            update produto
            set nome = coalesce(:nome, nome),
                tipo = coalesce(:tipo, tipo),
                preco = coalesce(:preco, preco)
            where id_produto = :id_produto
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(sql, {"nome": nome, "tipo": tipo, "preco": preco, "id_produto": id_produto})
            return True
        except Exception as e:
            self.logger.error(f"Error updating produto {id_produto}: {e}")
            return False

    def delete_produto(self, id_produto: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from produto where id_produto = :id_produto"), {"id_produto": id_produto})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting produto {id_produto}: {e}")
            return False

    # ------------------------------------------------------------------
    # ProdutoComercial (detalhe 1:1 de Produto, PK = FK)
    # ------------------------------------------------------------------
    def upsert_produto_comercial(
        self,
        id_produto: int,
        codigo_comercial: str | None = None,
        marca: str | None = None,
        descricao_comercial: str | None = None,
        conn=None,
    ) -> ProdutoComercialModel | None:
        sql = text(
            """
            insert into produto_comercial (id_produto, codigo_comercial, marca, descricao_comercial)
            values (:id_produto, :codigo_comercial, :marca, :descricao_comercial)
            on conflict (id_produto) do update
            set codigo_comercial = excluded.codigo_comercial,
                marca = excluded.marca,
                descricao_comercial = excluded.descricao_comercial
            """
        )
        params = {
            "id_produto": id_produto,
            "codigo_comercial": codigo_comercial,
            "marca": marca,
            "descricao_comercial": descricao_comercial,
        }
        try:
            with self._connection(conn) as c:
                c.execute(sql, params)
                return ProdutoComercialModel(**params)
        except Exception as e:
            self.logger.error(f"Error upserting produto_comercial for produto {id_produto}: {e}")
            return None

    def get_produto_comercial_by_produto(self, id_produto: int) -> ProdutoComercialModel | None:
        sql = text(
            "select id_produto, codigo_comercial, marca, descricao_comercial "
            "from produto_comercial where id_produto = :id_produto"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_produto": id_produto}).fetchone()
                return ProdutoComercialModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching produto_comercial for produto {id_produto}: {e}")
            return None

    def delete_produto_comercial(self, id_produto: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from produto_comercial where id_produto = :id_produto"), {"id_produto": id_produto}
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting produto_comercial for produto {id_produto}: {e}")
            return False

    # ------------------------------------------------------------------
    # Grao (detalhe 1:1 de Produto, PK = FK)
    # ------------------------------------------------------------------
    def upsert_grao(
        self,
        id_produto: int,
        umidade_maxima: Decimal | None = None,
        impureza_maxima: Decimal | None = None,
        classificacao_tipo: str | None = None,
        conn=None,
    ) -> GraoModel | None:
        sql = text(
            """
            insert into grao (id_produto, umidade_maxima, impureza_maxima, classificacao_tipo)
            values (:id_produto, :umidade_maxima, :impureza_maxima, :classificacao_tipo)
            on conflict (id_produto) do update
            set umidade_maxima = excluded.umidade_maxima,
                impureza_maxima = excluded.impureza_maxima,
                classificacao_tipo = excluded.classificacao_tipo
            """
        )
        params = {
            "id_produto": id_produto,
            "umidade_maxima": umidade_maxima,
            "impureza_maxima": impureza_maxima,
            "classificacao_tipo": classificacao_tipo,
        }
        try:
            with self._connection(conn) as c:
                c.execute(sql, params)
                return GraoModel(**params)
        except Exception as e:
            self.logger.error(f"Error upserting grao for produto {id_produto}: {e}")
            return None

    def get_grao_by_produto(self, id_produto: int) -> GraoModel | None:
        sql = text(
            "select id_produto, umidade_maxima, impureza_maxima, classificacao_tipo "
            "from grao where id_produto = :id_produto"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_produto": id_produto}).fetchone()
                return GraoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching grao for produto {id_produto}: {e}")
            return None

    def delete_grao(self, id_produto: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from grao where id_produto = :id_produto"), {"id_produto": id_produto})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting grao for produto {id_produto}: {e}")
            return False

    # ------------------------------------------------------------------
    # CotacaoGrao
    # ------------------------------------------------------------------
    def create_cotacao_grao(
        self, id_produto: int, data_cotacao: date, preco: Decimal, conn=None
    ) -> CotacaoGraoModel | None:
        sql = text(
            """
            insert into cotacao_grao (id_produto, data_cotacao, preco)
            values (:id_produto, :data_cotacao, :preco)
            returning id_cotacao
            """
        )
        params = {"id_produto": id_produto, "data_cotacao": data_cotacao, "preco": preco}
        try:
            with self._connection(conn) as c:
                id_cotacao = c.execute(sql, params).scalar_one()
                return CotacaoGraoModel(id_cotacao=id_cotacao, **params)
        except Exception as e:
            self.logger.error(f"Error creating cotacao_grao: {e}")
            return None

    def list_cotacoes_grao(self, filters: dict | None = None) -> list[CotacaoGraoModel]:
        where_sql, params = self._where_from_filters(filters, {"id_cotacao", "id_produto"})
        sql = text(
            f"select id_cotacao, id_produto, data_cotacao, preco from cotacao_grao {where_sql} order by data_cotacao desc"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [CotacaoGraoModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing cotacoes_grao: {e}")
            return []

    def delete_cotacao_grao(self, id_cotacao: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from cotacao_grao where id_cotacao = :id_cotacao"), {"id_cotacao": id_cotacao})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting cotacao_grao {id_cotacao}: {e}")
            return False

    # ------------------------------------------------------------------
    # Insumo (detalhe 1:1 de Produto, PK = FK)
    # ------------------------------------------------------------------
    def upsert_insumo(
        self,
        id_produto: int,
        classe_agronomica: str | None = None,
        principio_ativo: str | None = None,
        periodo_carencia_dias: int | None = None,
        registro_mapa: str | None = None,
        conn=None,
    ) -> InsumoModel | None:
        sql = text(
            """
            insert into insumo (id_produto, classe_agronomica, principio_ativo, periodo_carencia_dias, registro_mapa)
            values (:id_produto, :classe_agronomica, :principio_ativo, :periodo_carencia_dias, :registro_mapa)
            on conflict (id_produto) do update
            set classe_agronomica = excluded.classe_agronomica,
                principio_ativo = excluded.principio_ativo,
                periodo_carencia_dias = excluded.periodo_carencia_dias,
                registro_mapa = excluded.registro_mapa
            """
        )
        params = {
            "id_produto": id_produto,
            "classe_agronomica": classe_agronomica,
            "principio_ativo": principio_ativo,
            "periodo_carencia_dias": periodo_carencia_dias,
            "registro_mapa": registro_mapa,
        }
        try:
            with self._connection(conn) as c:
                c.execute(sql, params)
                return InsumoModel(**params)
        except Exception as e:
            self.logger.error(f"Error upserting insumo for produto {id_produto}: {e}")
            return None

    def get_insumo_by_produto(self, id_produto: int) -> InsumoModel | None:
        sql = text(
            "select id_produto, classe_agronomica, principio_ativo, periodo_carencia_dias, registro_mapa "
            "from insumo where id_produto = :id_produto"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_produto": id_produto}).fetchone()
                return InsumoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching insumo for produto {id_produto}: {e}")
            return None

    def delete_insumo(self, id_produto: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from insumo where id_produto = :id_produto"), {"id_produto": id_produto})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting insumo for produto {id_produto}: {e}")
            return False

    # ------------------------------------------------------------------
    # Certificacao
    # ------------------------------------------------------------------
    def create_certificacao(
        self, nome: str, orgao_emissor: str | None = None, tipo: str | None = None, conn=None
    ) -> CertificacaoModel | None:
        sql = text(
            """
            insert into certificacao (nome, orgao_emissor, tipo)
            values (:nome, :orgao_emissor, :tipo)
            returning id_certificacao
            """
        )
        params = {"nome": nome, "orgao_emissor": orgao_emissor, "tipo": tipo}
        try:
            with self._connection(conn) as c:
                id_certificacao = c.execute(sql, params).scalar_one()
                return CertificacaoModel(id_certificacao=id_certificacao, **params)
        except Exception as e:
            self.logger.error(f"Error creating certificacao: {e}")
            return None

    def get_certificacao_by_id(self, id_certificacao: int) -> CertificacaoModel | None:
        sql = text(
            "select id_certificacao, nome, orgao_emissor, tipo from certificacao where id_certificacao = :id_certificacao"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_certificacao": id_certificacao}).fetchone()
                return CertificacaoModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching certificacao {id_certificacao}: {e}")
            return None

    def list_certificacoes(self, filters: dict | None = None) -> list[CertificacaoModel]:
        where_sql, params = self._where_from_filters(filters, {"id_certificacao", "nome", "tipo"})
        sql = text(f"select id_certificacao, nome, orgao_emissor, tipo from certificacao {where_sql} order by nome")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [CertificacaoModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing certificacoes: {e}")
            return []

    def update_certificacao(
        self,
        id_certificacao: int,
        nome: str | None = None,
        orgao_emissor: str | None = None,
        tipo: str | None = None,
        conn=None,
    ) -> bool:
        sql = text(
            """
            update certificacao
            set nome = coalesce(:nome, nome),
                orgao_emissor = coalesce(:orgao_emissor, orgao_emissor),
                tipo = coalesce(:tipo, tipo)
            where id_certificacao = :id_certificacao
            """
        )
        try:
            with self._connection(conn) as c:
                c.execute(
                    sql,
                    {"nome": nome, "orgao_emissor": orgao_emissor, "tipo": tipo, "id_certificacao": id_certificacao},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating certificacao {id_certificacao}: {e}")
            return False

    def delete_certificacao(self, id_certificacao: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from certificacao where id_certificacao = :id_certificacao"),
                    {"id_certificacao": id_certificacao},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting certificacao {id_certificacao}: {e}")
            return False

    # ------------------------------------------------------------------
    # CertificacaoFazenda
    # ------------------------------------------------------------------
    def create_certificacao_fazenda(
        self,
        id_certificacao: int,
        id_fazenda: int,
        status: StatusCertificacao,
        dt_emissao: date | None = None,
        dt_validade: date | None = None,
        numero_certificado: str | None = None,
        conn=None,
    ) -> CertificacaoFazendaModel | None:
        sql = text(
            """
            insert into certificacao_fazenda (id_certificacao, id_fazenda, dt_emissao, dt_validade, numero_certificado, status)
            values (:id_certificacao, :id_fazenda, :dt_emissao, :dt_validade, :numero_certificado, :status)
            returning id_cert_fazenda
            """
        )
        params = {
            "id_certificacao": id_certificacao,
            "id_fazenda": id_fazenda,
            "dt_emissao": dt_emissao,
            "dt_validade": dt_validade,
            "numero_certificado": numero_certificado,
            "status": status.value,
        }
        try:
            with self._connection(conn) as c:
                id_cert_fazenda = c.execute(sql, params).scalar_one()
                return CertificacaoFazendaModel(id_cert_fazenda=id_cert_fazenda, **{**params, "status": status})
        except Exception as e:
            self.logger.error(f"Error creating certificacao_fazenda: {e}")
            return None

    def get_certificacao_fazenda_by_id(self, id_cert_fazenda: int) -> CertificacaoFazendaModel | None:
        sql = text(
            """
            select id_cert_fazenda, id_certificacao, id_fazenda, dt_emissao, dt_validade, numero_certificado, status
            from certificacao_fazenda where id_cert_fazenda = :id_cert_fazenda
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_cert_fazenda": id_cert_fazenda}).fetchone()
                return CertificacaoFazendaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching certificacao_fazenda {id_cert_fazenda}: {e}")
            return None

    def list_certificacoes_fazenda(self, filters: dict | None = None) -> list[CertificacaoFazendaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_cert_fazenda", "id_certificacao", "id_fazenda", "status"})
        sql = text(
            f"""
            select id_cert_fazenda, id_certificacao, id_fazenda, dt_emissao, dt_validade, numero_certificado, status
            from certificacao_fazenda {where_sql} order by id_cert_fazenda
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [CertificacaoFazendaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing certificacoes_fazenda: {e}")
            return []

    def update_status_certificacao_fazenda(self, id_cert_fazenda: int, status: StatusCertificacao, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update certificacao_fazenda set status = :status where id_cert_fazenda = :id_cert_fazenda"),
                    {"status": status.value, "id_cert_fazenda": id_cert_fazenda},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of certificacao_fazenda {id_cert_fazenda}: {e}")
            return False

    def delete_certificacao_fazenda(self, id_cert_fazenda: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from certificacao_fazenda where id_cert_fazenda = :id_cert_fazenda"),
                    {"id_cert_fazenda": id_cert_fazenda},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting certificacao_fazenda {id_cert_fazenda}: {e}")
            return False

    # ------------------------------------------------------------------
    # Cliente
    # ------------------------------------------------------------------
    def create_cliente(self, nome: str, documento: str, status: StatusCliente, conn=None) -> ClienteModel | None:
        """Cria a pessoa e o cliente numa unica transacao: o cadastro de cliente
        nao depende de uma pessoa pre-existente (nao ha, hoje, nenhuma tela para
        cadastrar pessoas soltas fora deste fluxo)."""
        sql_pessoa = text("insert into pessoa (nome, documento) values (:nome, :documento) returning id_pessoa")
        sql_cliente = text("insert into cliente (id_pessoa, status) values (:id_pessoa, :status) returning id_cliente")
        try:
            with self._connection(conn) as c:
                id_pessoa = c.execute(sql_pessoa, {"nome": nome, "documento": documento}).scalar_one()
                id_cliente = c.execute(sql_cliente, {"id_pessoa": id_pessoa, "status": status.value}).scalar_one()
                return ClienteModel(id_cliente=id_cliente, id_pessoa=id_pessoa, status=status, pessoa_nome=nome)
        except Exception as e:
            self.logger.error(f"Error creating cliente: {e}")
            return None

    def get_cliente_by_id(self, id_cliente: int) -> ClienteModel | None:
        sql = text(
            """
            select cliente.id_cliente as id_cliente, cliente.id_pessoa as id_pessoa,
                   cliente.status as status, pessoa.nome as pessoa_nome
            from cliente
            join pessoa on pessoa.id_pessoa = cliente.id_pessoa
            where cliente.id_cliente = :id_cliente
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_cliente": id_cliente}).fetchone()
                return ClienteModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching cliente {id_cliente}: {e}")
            return None

    def list_clientes(self) -> list[ClienteModel]:
        sql = text(
            """
            select cliente.id_cliente as id_cliente, cliente.id_pessoa as id_pessoa,
                   cliente.status as status, pessoa.nome as pessoa_nome
            from cliente
            join pessoa on pessoa.id_pessoa = cliente.id_pessoa
            order by pessoa.nome
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [ClienteModel(**row._mapping) for row in conn.execute(sql)]
        except Exception as e:
            self.logger.error(f"Error listing clientes: {e}")
            return []

    def update_status_cliente(self, id_cliente: int, status: StatusCliente, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("update cliente set status = :status where id_cliente = :id_cliente"),
                    {"status": status.value, "id_cliente": id_cliente},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error updating status of cliente {id_cliente}: {e}")
            return False

    def delete_cliente(self, id_cliente: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(text("delete from cliente where id_cliente = :id_cliente"), {"id_cliente": id_cliente})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting cliente {id_cliente}: {e}")
            return False

    # ------------------------------------------------------------------
    # Venda + ItemVenda (aggregate criado em uma unica transacao)
    # ------------------------------------------------------------------
    def create_venda_com_itens(
        self,
        id_cliente: int,
        id_centro_custo: int,
        valor_total: Decimal,
        itens: list[dict],
        data_venda: date | None = None,
        conn=None,
    ) -> tuple[VendaModel, list[ItemVendaModel]] | None:
        sql_venda = text(
            """
            insert into venda (id_cliente, id_centro_custo, valor_total, data_venda)
            values (:id_cliente, :id_centro_custo, :valor_total, :data_venda)
            returning id_venda
            """
        )
        sql_item = text(
            """
            insert into item_venda (id_venda, id_produto, id_lote, quantidade, valor_unitario)
            values (:id_venda, :id_produto, :id_lote, :quantidade, :valor_unitario)
            returning id_item_venda
            """
        )
        try:
            with self._connection(conn) as conn:
                id_venda = conn.execute(
                    sql_venda,
                    {
                        "id_cliente": id_cliente,
                        "id_centro_custo": id_centro_custo,
                        "valor_total": valor_total,
                        "data_venda": data_venda,
                    },
                ).scalar_one()

                itens_criados: list[ItemVendaModel] = []
                for item in itens:
                    item_params = {
                        "id_venda": id_venda,
                        "id_produto": item["id_produto"],
                        "id_lote": item.get("id_lote"),
                        "quantidade": item["quantidade"],
                        "valor_unitario": item["valor_unitario"],
                    }
                    id_item_venda = conn.execute(sql_item, item_params).scalar_one()
                    itens_criados.append(ItemVendaModel(id_item_venda=id_item_venda, **item_params))

                venda = VendaModel(
                    id_venda=id_venda,
                    id_cliente=id_cliente,
                    id_centro_custo=id_centro_custo,
                    valor_total=valor_total,
                    data_venda=data_venda,
                )
                return venda, itens_criados
        except Exception as e:
            self.logger.error(f"Error creating venda: {e}")
            return None

    def get_venda_by_id(self, id_venda: int) -> VendaModel | None:
        sql = text(
            "select id_venda, id_cliente, id_centro_custo, valor_total, data_venda from venda where id_venda = :id_venda"
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_venda": id_venda}).fetchone()
                return VendaModel(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching venda {id_venda}: {e}")
            return None

    def list_vendas(self, filters: dict | None = None) -> list[VendaModel]:
        where_sql, params = self._where_from_filters(filters, {"id_venda", "id_cliente", "id_centro_custo"})
        sql = text(
            f"""
            select id_venda, id_cliente, id_centro_custo, valor_total, data_venda
            from venda {where_sql} order by id_venda desc
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [VendaModel(**row._mapping) for row in conn.execute(sql, params)]
        except Exception as e:
            self.logger.error(f"Error listing vendas: {e}")
            return []

    def list_itens_por_venda(self, id_venda: int) -> list[ItemVendaModel]:
        sql = text(
            """
            select id_item_venda, id_venda, id_produto, id_lote, quantidade, valor_unitario
            from item_venda where id_venda = :id_venda order by id_item_venda
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [ItemVendaModel(**row._mapping) for row in conn.execute(sql, {"id_venda": id_venda})]
        except Exception as e:
            self.logger.error(f"Error listing itens for venda {id_venda}: {e}")
            return []

    # ------------------------------------------------------------------
    # Leituras auxiliares (lote pertence ao dominio Estoque) e lookups
    # ------------------------------------------------------------------
    def get_lote_info(self, id_lote: int) -> LoteInfo | None:
        sql = text("select id_lote, id_produto, codigo_lote, status from lote where id_lote = :id_lote")
        try:
            with self.pg_connector.pool.begin() as conn:
                row = conn.execute(sql, {"id_lote": id_lote}).fetchone()
                return LoteInfo(**row._mapping) if row else None
        except Exception as e:
            self.logger.error(f"Error fetching lote {id_lote}: {e}")
            return None

    def list_produto_options(self) -> list[ProdutoOption]:
        sql = text("select id_produto, nome from produto order by nome")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [ProdutoOption(**row._mapping) for row in conn.execute(sql)]
        except Exception as e:
            self.logger.error(f"Error listing produto options: {e}")
            return []

    def list_cliente_options(self) -> list[ClienteOption]:
        sql = text(
            """
            select cliente.id_cliente as id_cliente, pessoa.nome as nome
            from cliente
            join pessoa on pessoa.id_pessoa = cliente.id_pessoa
            where cliente.status = 'ATIVO'
            order by pessoa.nome
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [ClienteOption(**row._mapping) for row in conn.execute(sql)]
        except Exception as e:
            self.logger.error(f"Error listing cliente options: {e}")
            return []

    def list_centro_custo_options(self) -> list[CentroCustoOption]:
        sql = text("select id_centro_custo, nome from centro_custo order by nome")
        try:
            with self.pg_connector.pool.begin() as conn:
                return [CentroCustoOption(**row._mapping) for row in conn.execute(sql)]
        except Exception as e:
            self.logger.error(f"Error listing centro_custo options: {e}")
            return []

    def create_centro_custo(self, nome: str, conn=None) -> CentroCustoOption | None:
        sql = text("insert into centro_custo (nome) values (:nome) returning id_centro_custo")
        try:
            with self._connection(conn) as c:
                id_centro_custo = c.execute(sql, {"nome": nome}).scalar_one()
                return CentroCustoOption(id_centro_custo=id_centro_custo, nome=nome)
        except Exception as e:
            self.logger.error(f"Error creating centro_custo: {e}")
            return None

    def delete_centro_custo(self, id_centro_custo: int, conn=None) -> bool:
        try:
            with self._connection(conn) as c:
                c.execute(
                    text("delete from centro_custo where id_centro_custo = :id_centro_custo"),
                    {"id_centro_custo": id_centro_custo},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deleting centro_custo {id_centro_custo}: {e}")
            return False

    def list_lote_options(self) -> list[LoteOption]:
        sql = text(
            """
            select lote.id_lote as id_lote, lote.codigo_lote as codigo_lote,
                   produto.nome as produto_nome, lote.status as status
            from lote
            left join produto on produto.id_produto = lote.id_produto
            order by lote.codigo_lote
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                return [LoteOption(**row._mapping) for row in conn.execute(sql)]
        except Exception as e:
            self.logger.error(f"Error listing lote options: {e}")
            return []
