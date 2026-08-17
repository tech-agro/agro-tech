"""Acesso a dados do domínio estoque."""

from __future__ import annotations
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.compras.enum import OrderStatus
from app.compras.models.order import OrderModel
from app.compras.models.order_item import OrderItemModel
from app.compras.models.refs import ProdutoRef, UnidadeMedidaRef
from app.core.base_repository import BaseRepository
from app.core.database import get_session

from app.estoque.models.certificacao_lote import CertificacaoLoteModel
from app.estoque.models.estoque import EstoqueModel
from app.estoque.models.local_armazenamento import LocalArmazenamentoModel
from app.estoque.models.lote import LoteModel
from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel
from app.estoque.models.recebimento_compra import RecebimentoCompraModel
from app.estoque.models.refs import CertificacaoRef, ColheitaRef, CulturaRef, GraoRef, PlantioRef
from app.estoque.models.saldo_estoque import SaldoEstoqueModel
from app.estoque.models.saldo_lote import SaldoLoteModel


class LoteRepository(BaseRepository[LoteModel]):
    model = LoteModel

    def list_com_produto(self, limit: int = 50, offset: int = 0) -> list[tuple[LoteModel, str | None]]:
        """Lista lotes já trazendo o nome do produto associado (paginado)."""
        with get_session() as session:
            rows = session.execute(
                select(LoteModel, ProdutoRef.nome)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteModel.id_produto)
                .order_by(LoteModel.id_lote)
                .limit(limit)
                .offset(offset)
            ).all()
            result: list[tuple[LoteModel, str | None]] = []
            for lote, produto_nome in rows:
                session.expunge(lote)
                result.append((lote, produto_nome))
            return result

    def get_com_produto(self, id_lote: int) -> tuple[LoteModel, str | None] | None:
        """Busca um lote específico já trazendo o nome do produto associado."""
        with get_session() as session:
            row = session.execute(
                select(LoteModel, ProdutoRef.nome)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteModel.id_produto)
                .where(LoteModel.id_lote == id_lote)
            ).first()
            if row is None:
                return None
            lote, produto_nome = row
            session.expunge(lote)
            return lote, produto_nome

    def get_by_codigo(self, codigo_lote: str) -> LoteModel | None:
        """Busca um lote pelo código físico (etiqueta/documento)."""
        with get_session() as session:
            registro = session.scalars(
                select(LoteModel).where(LoteModel.codigo_lote == codigo_lote)
            ).first()
            if registro is not None:
                session.expunge(registro)
            return registro

    def list_proximos_vencimento(self, dias: int) -> list[LoteModel]:
        """Lista lotes cuja validade está dentro dos próximos N dias (não vencidos ainda)."""
        hoje = date.today()
        limite = hoje + timedelta(days=dias)
        with get_session() as session:
            registros = session.scalars(
                select(LoteModel).where(
                    LoteModel.validade.isnot(None),
                    LoteModel.validade >= hoje,
                    LoteModel.validade <= limite,
                )
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_vencidos(self) -> list[LoteModel]:
        """Lista lotes cuja validade já passou (vencidos)."""
        hoje = date.today()
        with get_session() as session:
            registros = session.scalars(
                select(LoteModel).where(
                    LoteModel.validade.isnot(None),
                    LoteModel.validade < hoje,
                )
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)


class LocalArmazenamentoRepository(BaseRepository[LocalArmazenamentoModel]):
    model = LocalArmazenamentoModel

    def list_ocupacao(self) -> list[tuple[LocalArmazenamentoModel, Decimal]]:
        """Ocupacao total (soma dos saldos de estoque) por local, para comparar com a capacidade."""
        with get_session() as session:
            rows = session.execute(
                select(
                    LocalArmazenamentoModel,
                    func.coalesce(func.sum(SaldoEstoqueModel.quantidade_atual), 0),
                )
                .select_from(LocalArmazenamentoModel)
                .outerjoin(
                    EstoqueModel, EstoqueModel.id_local == LocalArmazenamentoModel.id_local
                )
                .outerjoin(
                    SaldoEstoqueModel, SaldoEstoqueModel.id_estoque == EstoqueModel.id_estoque
                )
                .group_by(LocalArmazenamentoModel.id_local)
                .order_by(LocalArmazenamentoModel.descricao)
            ).all()
            result: list[tuple[LocalArmazenamentoModel, Decimal]] = []
            for local, ocupado in rows:
                session.expunge(local)
                result.append((local, Decimal(str(ocupado))))
            return result


class EstoqueRepository(BaseRepository[EstoqueModel]):
    model = EstoqueModel

    def list_com_local(self) -> list[tuple[EstoqueModel, str | None]]:
        """Lista estoques já trazendo a descrição do local associado."""
        with get_session() as session:
            rows = session.execute(
                select(EstoqueModel, LocalArmazenamentoModel.descricao)
                .outerjoin(
                    LocalArmazenamentoModel,
                    LocalArmazenamentoModel.id_local == EstoqueModel.id_local,
                )
                .order_by(EstoqueModel.id_estoque)
            ).all()
            result: list[tuple[EstoqueModel, str | None]] = []
            for estoque, local_descricao in rows:
                session.expunge(estoque)
                result.append((estoque, local_descricao))
            return result

    def list_by_local(self, id_local: int) -> list[EstoqueModel]:
        """Lista os estoques de um local de armazenamento específico."""
        with get_session() as session:
            registros = session.scalars(
                select(EstoqueModel).where(EstoqueModel.id_local == id_local)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def exists_by_local(self, id_local: int) -> bool:
        """Verifica se o local possui estoques cadastrados."""
        with get_session() as session:
            return (
                session.scalar(
                    select(EstoqueModel.id_estoque)
                    .where(EstoqueModel.id_local == id_local)
                    .limit(1)
                )
                is not None
            )

    def get_com_local(self, id_estoque: int) -> tuple[EstoqueModel, str | None] | None:
        """Obtém um estoque trazendo também a descrição do local."""
        with get_session() as session:
            row = session.execute(
                select(EstoqueModel, LocalArmazenamentoModel.descricao)
                .outerjoin(
                    LocalArmazenamentoModel,
                    LocalArmazenamentoModel.id_local == EstoqueModel.id_local,
                )
                .where(EstoqueModel.id_estoque == id_estoque)
            ).first()

            if row is None:
                return None

            estoque, local_descricao = row
            session.expunge(estoque)
            return estoque, local_descricao


class CertificacaoLoteRepository(BaseRepository[CertificacaoLoteModel]):
    model = CertificacaoLoteModel

    def list_paginado(self, limit: int = 50, offset: int = 0) -> list[CertificacaoLoteModel]:
        """Lista todas as certificações do sistema, paginado."""
        with get_session() as session:
            registros = session.scalars(
                select(CertificacaoLoteModel)
                .order_by(CertificacaoLoteModel.id_cert_lote)
                .limit(limit)
                .offset(offset)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_by_lote_com_detalhes(
        self, id_lote: int
    ) -> list[tuple[CertificacaoLoteModel, str | None, str | None]]:
        """Lista certificações de um lote, já com código do lote e nome da certificação."""
        with get_session() as session:
            rows = session.execute(
                select(CertificacaoLoteModel, LoteModel.codigo_lote, CertificacaoRef.nome)
                .outerjoin(LoteModel, LoteModel.id_lote == CertificacaoLoteModel.id_lote)
                .outerjoin(
                    CertificacaoRef,
                    CertificacaoRef.id_certificacao == CertificacaoLoteModel.id_certificacao,
                )
                .where(CertificacaoLoteModel.id_lote == id_lote)
                .order_by(CertificacaoLoteModel.dt_emissao)
            ).all()
            result: list[tuple[CertificacaoLoteModel, str | None, str | None]] = []
            for cert, lote_codigo, certificacao_nome in rows:
                session.expunge(cert)
                result.append((cert, lote_codigo, certificacao_nome))
            return result

    def exists_by_lote(self, id_lote: int) -> bool:
        """Verifica se o lote possui certificações cadastradas."""
        with get_session() as session:
            return (
                session.scalar(
                    select(CertificacaoLoteModel.id_cert_lote)
                    .where(CertificacaoLoteModel.id_lote == id_lote)
                    .limit(1)
                )
                is not None
            )

    def get_by_certificacao_lote(
        self,
        id_certificacao: int,
        id_lote: int,
    ) -> CertificacaoLoteModel | None:
        """Busca o vínculo entre uma certificação e um lote."""
        with get_session() as session:
            registro = session.scalars(
                select(CertificacaoLoteModel).where(
                    CertificacaoLoteModel.id_certificacao == id_certificacao,
                    CertificacaoLoteModel.id_lote == id_lote,
                )
            ).first()

            if registro is not None:
                session.expunge(registro)

            return registro


class SaldoEstoqueRepository(BaseRepository[SaldoEstoqueModel]):
    """Somente leitura pela API — a escrita é feita pelo service a partir de movimentações."""

    model = SaldoEstoqueModel

    def get_by_estoque_produto(self, id_estoque: int, id_produto: int) -> SaldoEstoqueModel | None:
        """Busca o saldo de um produto específico em um estoque específico."""
        with get_session() as session:
            registro = session.scalars(
                select(SaldoEstoqueModel).where(
                    SaldoEstoqueModel.id_estoque == id_estoque,
                    SaldoEstoqueModel.id_produto == id_produto,
                )
            ).first()
            if registro is not None:
                session.expunge(registro)
            return registro

    def list_by_estoque(self, id_estoque: int) -> list[SaldoEstoqueModel]:
        """Lista todos os saldos de um estoque (visão geral do que há armazenado)."""
        with get_session() as session:
            registros = session.scalars(
                select(SaldoEstoqueModel).where(SaldoEstoqueModel.id_estoque == id_estoque)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_by_produto(self, id_produto: int) -> list[SaldoEstoqueModel]:
        """Lista o saldo de um produto em todos os estoques (visão geral do produto)."""
        with get_session() as session:
            registros = session.scalars(
                select(SaldoEstoqueModel).where(SaldoEstoqueModel.id_produto == id_produto)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_by_estoque_com_produto(
        self, id_estoque: int
    ) -> list[tuple[SaldoEstoqueModel, str | None]]:
        """Lista saldos de um estoque, já trazendo o nome do produto."""
        with get_session() as session:
            rows = session.execute(
                select(SaldoEstoqueModel, ProdutoRef.nome)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == SaldoEstoqueModel.id_produto)
                .where(SaldoEstoqueModel.id_estoque == id_estoque)
            ).all()
            result: list[tuple[SaldoEstoqueModel, str | None]] = []
            for saldo, produto_nome in rows:
                session.expunge(saldo)
                result.append((saldo, produto_nome))
            return result

    def exists_by_estoque(self, id_estoque: int) -> bool:
        """Verifica se o estoque possui saldos cadastrados."""
        with get_session() as session:
            return (
                session.scalar(
                    select(SaldoEstoqueModel.id_estoque)
                    .where(SaldoEstoqueModel.id_estoque == id_estoque)
                    .limit(1)
                )
                is not None
            )


class SaldoLoteRepository(BaseRepository[SaldoLoteModel]):
    model = SaldoLoteModel

    def get_by_estoque_lote(
        self, id_estoque: int, id_lote: int
    ) -> SaldoLoteModel | None:
        with get_session() as session:
            record = (
                session.query(SaldoLoteModel)
                .filter_by(id_estoque=id_estoque, id_lote=id_lote)
                .first()
            )
            if record is not None:
                session.expunge(record)
            return record

    def list_available_by_produto(
        self, id_produto: int
    ) -> list[tuple[SaldoLoteModel, str, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(SaldoLoteModel, LoteModel.codigo_lote, ProdutoRef.nome)
                .select_from(SaldoLoteModel)
                .join(LoteModel, LoteModel.id_lote == SaldoLoteModel.id_lote)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteModel.id_produto)
                .where(LoteModel.id_produto == id_produto)
                .where(SaldoLoteModel.quantidade_atual > SaldoLoteModel.quantidade_reservada)
                .order_by(LoteModel.codigo_lote)
            ).all()
            result: list[tuple[SaldoLoteModel, str, str | None]] = []
            for saldo, codigo, nome in rows:
                session.expunge(saldo)
                result.append((saldo, codigo, nome))
            return result

    def list_localizacoes(self) -> list[tuple[SaldoLoteModel, str, str | None, str]]:
        """Onde cada lote com saldo positivo esta guardado (lote -> estoque -> local)."""
        with get_session() as session:
            rows = session.execute(
                select(
                    SaldoLoteModel,
                    LoteModel.codigo_lote,
                    ProdutoRef.nome,
                    LocalArmazenamentoModel.descricao,
                )
                .select_from(SaldoLoteModel)
                .join(LoteModel, LoteModel.id_lote == SaldoLoteModel.id_lote)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteModel.id_produto)
                .join(EstoqueModel, EstoqueModel.id_estoque == SaldoLoteModel.id_estoque)
                .join(
                    LocalArmazenamentoModel,
                    LocalArmazenamentoModel.id_local == EstoqueModel.id_local,
                )
                .where(SaldoLoteModel.quantidade_atual > 0)
                .order_by(LocalArmazenamentoModel.descricao, LoteModel.codigo_lote)
            ).all()
            result: list[tuple[SaldoLoteModel, str, str | None, str]] = []
            for saldo, codigo, produto_nome, local_descricao in rows:
                session.expunge(saldo)
                result.append((saldo, codigo, produto_nome, local_descricao))
            return result


class MovimentacaoEstoqueRepository(BaseRepository[MovimentacaoEstoqueModel]):
    """Somente leitura pela API — a criação é feita pelo service, nunca diretamente."""

    model = MovimentacaoEstoqueModel

    def list_by_estoque(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueModel]:
        """Histórico de movimentações de um estoque, mais recentes primeiro (paginado)."""
        with get_session() as session:
            registros = session.scalars(
                select(MovimentacaoEstoqueModel)
                .where(MovimentacaoEstoqueModel.id_estoque == id_estoque)
                .order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_by_lote(
        self, id_lote: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueModel]:
        """Histórico de movimentações de um lote específico (rastreabilidade, paginado)."""
        with get_session() as session:
            registros = session.scalars(
                select(MovimentacaoEstoqueModel)
                .where(MovimentacaoEstoqueModel.id_lote == id_lote)
                .order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_by_estoque_com_produto(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[tuple[MovimentacaoEstoqueModel, str | None, str | None]]:
        """Histórico de movimentações de um estoque, já trazendo o nome do produto e o código do lote (paginado)."""
        with get_session() as session:
            rows = session.execute(
                select(MovimentacaoEstoqueModel, ProdutoRef.nome, LoteModel.codigo_lote)
                .select_from(MovimentacaoEstoqueModel)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == MovimentacaoEstoqueModel.id_produto)
                .outerjoin(LoteModel, LoteModel.id_lote == MovimentacaoEstoqueModel.id_lote)
                .where(MovimentacaoEstoqueModel.id_estoque == id_estoque)
                .order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            result: list[tuple[MovimentacaoEstoqueModel, str | None, str | None]] = []
            for mov, produto_nome, lote_codigo in rows:
                session.expunge(mov)
                result.append((mov, produto_nome, lote_codigo))
            return result

    def list_by_estoque_periodo(
        self,
        id_estoque: int,
        data_inicio: datetime,
        data_fim: datetime,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovimentacaoEstoqueModel]:
        """Movimentações de um estoque num intervalo de datas (paginado)."""
        with get_session() as session:
            registros = session.scalars(
                select(MovimentacaoEstoqueModel)
                .where(
                    MovimentacaoEstoqueModel.id_estoque == id_estoque,
                    MovimentacaoEstoqueModel.data_movimentacao.between(data_inicio, data_fim),
                )
                .order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def exists_by_estoque(self, id_estoque: int) -> bool:
        """Verifica se o estoque possui movimentações registradas."""
        with get_session() as session:
            return (
                session.scalar(
                    select(MovimentacaoEstoqueModel.id_movimentacao)
                    .where(MovimentacaoEstoqueModel.id_estoque == id_estoque)
                    .limit(1)
                )
                is not None
            )

    def exists_by_lote(self, id_lote: int) -> bool:
        """Verifica se o lote possui movimentações registradas."""
        with get_session() as session:
            return (
                session.scalar(
                    select(MovimentacaoEstoqueModel.id_movimentacao)
                    .where(MovimentacaoEstoqueModel.id_lote == id_lote)
                    .limit(1)
                )
                is not None
            )


class RecebimentoCompraRepository(BaseRepository[RecebimentoCompraModel]):
    model = RecebimentoCompraModel

    def list_by_item_pedido(self, id_item_pedido: int) -> list[RecebimentoCompraModel]:
        """Lista os recebimentos já registrados para um item de pedido (pode haver mais de um, em entregas parciais)."""
        with get_session() as session:
            registros = session.scalars(
                select(RecebimentoCompraModel)
                .where(RecebimentoCompraModel.id_item_pedido == id_item_pedido)
                .order_by(RecebimentoCompraModel.data_recebimento)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def total_recebido_por_item(self, id_item_pedido: int) -> Decimal:
        """Soma tudo que já foi recebido para um item (para comparar com a quantidade pedida)."""
        with get_session() as session:
            total = session.scalar(
                select(func.coalesce(func.sum(RecebimentoCompraModel.quantidade_recebida), 0))
                .where(RecebimentoCompraModel.id_item_pedido == id_item_pedido)
            )
            return total or Decimal("0")

    def list_by_estoque(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[RecebimentoCompraModel]:
        """Recebimentos registrados em um estoque, mais recentes primeiro (paginado)."""
        with get_session() as session:
            registros = session.scalars(
                select(RecebimentoCompraModel)
                .where(RecebimentoCompraModel.id_estoque == id_estoque)
                .order_by(RecebimentoCompraModel.data_recebimento.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)


class LookupRepository:
    """Consultas utilizadas para preencher comboboxes e selects no frontend."""

    def list_produtos(self) -> list[tuple[int, str, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(ProdutoRef.id_produto, ProdutoRef.nome, UnidadeMedidaRef.sigla)
                .outerjoin(
                    UnidadeMedidaRef,
                    UnidadeMedidaRef.id_unidade == ProdutoRef.id_unidade,
                )
                .order_by(ProdutoRef.nome)
            ).all()
            result: list[tuple[int, str, str | None]] = []
            for id_produto, nome, sigla in rows:
                unidade = sigla.value if hasattr(sigla, "value") else sigla
                result.append((id_produto, nome, str(unidade) if unidade else None))
            return result

    def list_colheitas(self) -> list[tuple[int, str]]:
        with get_session() as session:
            rows = session.execute(
                select(ColheitaRef.id_colheita, ColheitaRef.dt_fim).order_by(
                    ColheitaRef.id_colheita.desc()
                )
            ).all()
            return [
                (
                    id_colheita,
                    f"Colheita #{id_colheita} ({dt_fim:%d/%m/%Y})"
                    if dt_fim is not None
                    else f"Colheita #{id_colheita} (em andamento)",
                )
                for id_colheita, dt_fim in rows
            ]

    def list_locais(self) -> list[tuple[int, str]]:
        with get_session() as session:
            rows = session.execute(
                select(LocalArmazenamentoModel.id_local, LocalArmazenamentoModel.descricao)
                .order_by(LocalArmazenamentoModel.descricao)
            ).all()
            return [(id_local, descricao) for id_local, descricao in rows]

    def list_estoques(self) -> list[tuple[int, str]]:
        with get_session() as session:
            rows = session.execute(
                select(EstoqueModel.id_estoque, LocalArmazenamentoModel.descricao)
                .join(
                    LocalArmazenamentoModel,
                    LocalArmazenamentoModel.id_local == EstoqueModel.id_local,
                )
                .order_by(LocalArmazenamentoModel.descricao)
            ).all()
            return [(id_estoque, descricao) for id_estoque, descricao in rows]

    def list_lotes(self) -> list[tuple[int, str, int | None, str | None]]:
        with get_session() as session:
            rows = session.execute(
                select(
                    LoteModel.id_lote,
                    LoteModel.codigo_lote,
                    LoteModel.id_produto,
                    ProdutoRef.nome,
                )
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteModel.id_produto)
                .order_by(LoteModel.codigo_lote)
            ).all()
            return [
                (id_lote, codigo_lote, id_produto, produto_nome)
                for id_lote, codigo_lote, id_produto, produto_nome in rows
            ]

    def list_certificacoes(self) -> list[tuple[int, str]]:
        with get_session() as session:
            rows = session.execute(
                select(CertificacaoRef.id_certificacao, CertificacaoRef.nome)
                .order_by(CertificacaoRef.nome)
            ).all()
            return [(id_certificacao, nome) for id_certificacao, nome in rows]

    def list_itens_pedido_pendentes(self) -> list[tuple[int, int | None, str]]:
        """Itens de pedido ainda não totalmente atendidos, candidatos a recebimento."""
        with get_session() as session:
            rows = session.execute(
                select(
                    OrderItemModel.id_item,
                    OrderItemModel.id_produto,
                    ProdutoRef.nome,
                    OrderItemModel.quantidade,
                )
                .join(OrderModel, OrderModel.id_pedido == OrderItemModel.id_pedido)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == OrderItemModel.id_produto)
                .where(
                    OrderModel.status.in_(
                        [OrderStatus.APROVADO, OrderStatus.PARCIALMENTE_ATENDIDO]
                    )
                )
                .order_by(OrderItemModel.id_item.desc())
            ).all()
            return [
                (
                    id_item,
                    id_produto,
                    f"{produto_nome or 'Produto desconhecido'} — pedido de {quantidade}",
                )
                for id_item, id_produto, produto_nome, quantidade in rows
            ]