"""Acesso a dados do domínio estoque."""

from __future__ import annotations
from datetime import datetime, date, timedelta

from sqlalchemy import select

from app.compras.models.refs import ProdutoRef
from app.core.base_repository import BaseRepository
from app.core.database import get_session

from app.estoque.models.certificacao_lote import CertificacaoLoteModel
from app.estoque.models.estoque import EstoqueModel
from app.estoque.models.local_armazenamento import LocalArmazenamentoModel
from app.estoque.models.lote import LoteModel
from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel
from app.estoque.models.refs import CertificacaoRef
from app.estoque.models.saldo_estoque import SaldoEstoqueModel


class LoteRepository(BaseRepository[LoteModel]):
    model = LoteModel

    def list_com_produto(self) -> list[tuple[LoteModel, str | None]]:
        """Lista lotes já trazendo o nome do produto associado."""
        with get_session() as session:
            rows = session.execute(
                select(LoteModel, ProdutoRef.nome)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == LoteModel.id_produto)
                .order_by(LoteModel.id_lote)
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


class CertificacaoLoteRepository(BaseRepository[CertificacaoLoteModel]):
    model = CertificacaoLoteModel

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
    ) -> list[tuple[MovimentacaoEstoqueModel, str | None]]:
        """Histórico de movimentações de um estoque, já trazendo o nome do produto (paginado)."""
        with get_session() as session:
            rows = session.execute(
                select(MovimentacaoEstoqueModel, ProdutoRef.nome)
                .outerjoin(ProdutoRef, ProdutoRef.id_produto == MovimentacaoEstoqueModel.id_produto)
                .where(MovimentacaoEstoqueModel.id_estoque == id_estoque)
                .order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
                .limit(limit)
                .offset(offset)
            ).all()
            result: list[tuple[MovimentacaoEstoqueModel, str | None]] = []
            for mov, produto_nome in rows:
                session.expunge(mov)
                result.append((mov, produto_nome))
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