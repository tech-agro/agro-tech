"""Regras de negócio do domínio estoque."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.compras.enum import OrderStatus
from app.compras.models.refs import ProdutoRef
from app.compras.repository import OrderItemRepository, OrderRepository, PurchaseRepository
from app.core.database import get_session, pg_connector

from app.estoque.errors import EstoqueError
from app.estoque.enum import LotOriginType, MovementType, StatusLote
from app.estoque.models.entrada_colheita_estoque import EntradaColheitaEstoqueModel
from app.estoque.models.entrada_estoque import EntradaEstoqueModel
from app.estoque.models.estoque import EstoqueModel
from app.estoque.models.lote import LoteModel
from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel
from app.estoque.models.recebimento_compra import RecebimentoCompraModel
from app.estoque.models.refs import ColheitaRef, CulturaRef, GraoRef, PlantioRef
from app.estoque.models.saida_estoque import SaidaEstoqueModel
from app.estoque.models.saldo_estoque import SaldoEstoqueModel
from app.estoque.models.saldo_lote import SaldoLoteModel
from app.estoque.repository import (
    CertificacaoLoteRepository,
    EstoqueRepository,
    LocalArmazenamentoRepository,
    LookupRepository,
    LoteRepository,
    MovimentacaoEstoqueRepository,
    RecebimentoCompraRepository,
    SaldoEstoqueRepository,
    SaldoLoteRepository,
)
from app.estoque.schemas.certificacao_lote import CertificacaoLoteCreateSchema, CertificacaoLoteReadSchema, CertificacaoLoteUpdateSchema
from app.estoque.schemas.entrada_colheita_estoque import EntradaColheitaCreateSchema, EntradaColheitaReadSchema
from app.estoque.schemas.estoque import EstoqueCreateSchema, EstoqueReadSchema
from app.estoque.schemas.local_armazenamento import LocalArmazenamentoCreateSchema, LocalArmazenamentoReadSchema, LocalArmazenamentoUpdateSchema
from app.estoque.schemas.lookups import CertificacaoOptionSchema, ColheitaOptionSchema, EstoqueOptionSchema, ItemPedidoOptionSchema, LocalArmazenamentoOptionSchema, LoteOptionSchema, ProdutoOptionSchema
from app.estoque.schemas.lote import LoteCreateSchema, LoteReadSchema, LoteUpdateSchema
from app.estoque.schemas.movimentacao_estoque import MovimentacaoEstoqueReadSchema
from app.estoque.schemas.recebimento_compra import (
    RecebimentoCompraCreateSchema,
    RecebimentoCompraReadSchema,
)
from app.estoque.schemas.saldo_estoque import SaldoEstoqueReadSchema
from app.estoque.schemas.saldo_lote import SaldoLoteReadSchema


class EstoqueService:
    """Camada de orquestração das regras de negócio do estoque."""

    def __init__(
        self,
        lote_repo: LoteRepository | None = None,
        local_repo: LocalArmazenamentoRepository | None = None,
        estoque_repo: EstoqueRepository | None = None,
        certificacao_repo: CertificacaoLoteRepository | None = None,
        saldo_repo: SaldoEstoqueRepository | None = None,
        saldo_lote_repo: SaldoLoteRepository | None = None,
        movimentacao_repo: MovimentacaoEstoqueRepository | None = None,
        recebimento_repo: RecebimentoCompraRepository | None = None,
        lookup_repo: LookupRepository | None = None,
        order_repo: OrderRepository | None = None,
        order_item_repo: OrderItemRepository | None = None,
        purchase_repo: PurchaseRepository | None = None,
    ) -> None:
        self.lote_repo = lote_repo or LoteRepository()
        self.local_repo = local_repo or LocalArmazenamentoRepository()
        self.estoque_repo = estoque_repo or EstoqueRepository()
        self.certificacao_repo = certificacao_repo or CertificacaoLoteRepository()
        self.saldo_repo = saldo_repo or SaldoEstoqueRepository()
        self.saldo_lote_repo = saldo_lote_repo or SaldoLoteRepository()
        self.movimentacao_repo = movimentacao_repo or MovimentacaoEstoqueRepository()
        self.recebimento_repo = recebimento_repo or RecebimentoCompraRepository()
        self.lookup_repo = lookup_repo or LookupRepository()
        self.order_repo = order_repo or OrderRepository()
        self.order_item_repo = order_item_repo or OrderItemRepository()
        self.purchase_repo = purchase_repo or PurchaseRepository()

    @staticmethod
    def _create_lote_auto(
        session: Session,
        *,
        id_produto: int,
        tipo_origem: LotOriginType,
        id_colheita: int | None = None,
        validade: date | None = None,
        qualidade: str | None = None,
        quantidade_inicial: Decimal | None = None,
        status: StatusLote = StatusLote.LIBERADO,
        prefix: str = "LOTE",
    ) -> LoteModel:
        """Persist a lot and assign codigo_lote = LOTE-{id} after flush."""
        lote = LoteModel(
            id_colheita=id_colheita,
            id_produto=id_produto,
            codigo_lote=f"TMP-{uuid4().hex}",
            validade=validade,
            qualidade=qualidade,
            tipo_origem=tipo_origem,
            quantidade_inicial=quantidade_inicial,
            status=status,
        )
        session.add(lote)
        session.flush()
        lote.codigo_lote = f"{prefix}-{lote.id_lote}"
        return lote

    # ------------------------------------------------------------------
    # Hooks chamados por outros Módulos
    # ------------------------------------------------------------------

    def register_entry_from_purchase(self, id_compra: int) -> None:
        """No-op: physical receipt happens via registrar_recebimento."""
        return None

    def register_entry_from_harvest(
        self,
        id_colheita: int,
        *,
        id_estoque: int | None = None,
        id_produto: int | None = None,
        quantidade: Decimal | None = None,
    ) -> EntradaColheitaReadSchema | None:
        """Called by production when a harvest is concluded.

        Resolves product (grain matching culture name when possible), default
        warehouse, and auto-generates the lot code.
        Skips if an entry already exists for this harvest.
        """
        with get_session() as session:
            existing = session.execute(
                select(EntradaColheitaEstoqueModel).where(
                    EntradaColheitaEstoqueModel.id_colheita == id_colheita
                )
            ).scalars().first()
            if existing is not None:
                return None

            colheita = session.get(ColheitaRef, id_colheita)
            if colheita is None:
                raise EstoqueError("Harvest not found.")

            resolved_qty = quantidade
            if resolved_qty is None and colheita.quantidade_colhida is not None:
                resolved_qty = Decimal(str(colheita.quantidade_colhida))
            if resolved_qty is None or resolved_qty <= 0:
                raise EstoqueError(
                    "Harvest has no quantity; cannot register stock entry."
                )

            resolved_product = id_produto
            if resolved_product is None:
                resolved_product = self._resolve_harvest_product(
                    session, colheita.id_plantio
                )
            if resolved_product is None:
                raise EstoqueError(
                    "Could not resolve harvested product; pass id_produto."
                )

            resolved_estoque = id_estoque
            if resolved_estoque is None:
                first = session.execute(
                    select(EstoqueModel.id_estoque).order_by(EstoqueModel.id_estoque)
                ).scalars().first()
                if first is None:
                    raise EstoqueError("No warehouse stock account configured.")
                resolved_estoque = int(first)

        return self.registrar_entrada_colheita(
            EntradaColheitaCreateSchema(
                id_colheita=id_colheita,
                id_produto=resolved_product,
                id_estoque=resolved_estoque,
                quantidade=resolved_qty,
            )
        )

    @staticmethod
    def _resolve_harvest_product(session: Session, id_plantio: int) -> int | None:
        """Prefer grain whose name matches the culture; fallback to planting product."""
        plantio = session.get(PlantioRef, id_plantio)
        if plantio is None:
            return None
        cultura = session.get(CulturaRef, plantio.id_cultura)
        if cultura is not None:
            row = session.execute(
                select(ProdutoRef.id_produto)
                .join(GraoRef, GraoRef.id_produto == ProdutoRef.id_produto)
                .where(func.lower(ProdutoRef.nome) == cultura.nome.lower())
            ).scalars().first()
            if row is not None:
                return int(row)
            # partial match (e.g. culture "Milho Hibrido" vs product "Milho")
            row = session.execute(
                select(ProdutoRef.id_produto)
                .join(GraoRef, GraoRef.id_produto == ProdutoRef.id_produto)
                .where(func.lower(ProdutoRef.nome).like(f"%{cultura.nome.lower().split()[0]}%"))
            ).scalars().first()
            if row is not None:
                return int(row)
        return int(plantio.id_produto)

    def register_exit_from_sale(self, id_item_venda: int) -> None:
        """Legacy hook: prefer register_exit_from_sale_allocation."""
        return None

    def register_exit_from_sale_allocation(
        self,
        *,
        id_item_venda: int,
        id_estoque: int,
        id_produto: int,
        id_lote: int,
        quantidade: Decimal,
    ) -> MovimentacaoEstoqueReadSchema:
        """Called by Commercial when a sale is confirmed (per lot allocation)."""
        return self.registrar_saida_venda(
            id_estoque=id_estoque,
            id_produto=id_produto,
            id_item_venda=id_item_venda,
            quantidade=quantidade,
            id_lote=id_lote,
        )

    def register_exit_from_activity(self, id_atividade: int) -> None:
        """Placeholder until agricultural activities push consumption details."""
        return None

    def register_transfer(
        self,
        *,
        id_estoque_origem: int,
        id_estoque_destino: int,
        id_produto: int,
        id_lote: int,
        quantidade: Decimal,
    ) -> tuple[MovimentacaoEstoqueReadSchema, MovimentacaoEstoqueReadSchema]:
        """Transfer quantity of a lot between stock accounts (logistics TRANSFERENCIA)."""
        if id_estoque_origem == id_estoque_destino:
            raise EstoqueError("Origin and destination stock must differ.")
        self._assert_saldo_lote(id_estoque_origem, id_lote, quantidade)

        try:
            with get_session() as session:
                saida = MovimentacaoEstoqueModel(
                    id_estoque=id_estoque_origem,
                    id_produto=id_produto,
                    id_lote=id_lote,
                    tipo_movimentacao=MovementType.TRANSFERENCIA.value,
                    quantidade=quantidade,
                    data_movimentacao=datetime.now(),
                )
                session.add(saida)
                session.flush()
                self._ajustar_saldo(session, id_estoque_origem, id_produto, -quantidade)
                self._ajustar_saldo_lote(session, id_estoque_origem, id_lote, -quantidade)

                entrada = MovimentacaoEstoqueModel(
                    id_estoque=id_estoque_destino,
                    id_produto=id_produto,
                    id_lote=id_lote,
                    tipo_movimentacao=MovementType.TRANSFERENCIA.value,
                    quantidade=quantidade,
                    data_movimentacao=datetime.now(),
                )
                session.add(entrada)
                session.flush()
                self._ajustar_saldo(session, id_estoque_destino, id_produto, quantidade)
                self._ajustar_saldo_lote(session, id_estoque_destino, id_lote, quantidade)
                session.flush()
                id_saida = saida.id_movimentacao
                id_entrada = entrada.id_movimentacao
        except IntegrityError as exc:
            raise EstoqueError("Could not register stock transfer.") from exc

        out = self.movimentacao_repo.get_by_id(id_saida)
        inn = self.movimentacao_repo.get_by_id(id_entrada)
        if out is None or inn is None:
            raise EstoqueError("Transfer movements not found after insert.")
        return (
            MovimentacaoEstoqueReadSchema.model_validate(out),
            MovimentacaoEstoqueReadSchema.model_validate(inn),
        )

    def register_exit_from_dispatch(
        self,
        *,
        id_estoque: int,
        id_produto: int,
        id_lote: int,
        quantidade: Decimal,
        id_item_venda: int | None = None,
    ) -> MovimentacaoEstoqueReadSchema | None:
        """Called by logistics when a load is shipped.

        If the sale already exited stock on confirm, skip duplicate exit.
        """
        if id_item_venda is not None:
            with get_session() as session:
                existing = session.execute(
                    select(SaidaVendaEstoqueModel).where(
                        SaidaVendaEstoqueModel.id_item_venda == id_item_venda
                    )
                ).scalars().first()
                if existing is not None:
                    return None
            return self.registrar_saida_venda(
                id_estoque=id_estoque,
                id_produto=id_produto,
                id_item_venda=id_item_venda,
                quantidade=quantidade,
                id_lote=id_lote,
            )
        # Non-sale dispatch: ledger exit without sale satellite (transfer-like).
        return self._registrar_saida_simples(
            id_estoque=id_estoque,
            id_produto=id_produto,
            id_lote=id_lote,
            quantidade=quantidade,
            tipo=MovementType.TRANSFERENCIA.value,
        )

    def _registrar_saida_simples(
        self,
        *,
        id_estoque: int,
        id_produto: int,
        id_lote: int | None,
        quantidade: Decimal,
        tipo: str,
    ) -> MovimentacaoEstoqueReadSchema:
        if id_lote is not None:
            self._assert_saldo_lote(id_estoque, id_lote, quantidade)
        else:
            saldo = self.saldo_repo.get_by_estoque_produto(id_estoque, id_produto)
            if saldo is None or saldo.quantidade_atual < quantidade:
                raise EstoqueError("Insufficient stock balance for exit.")

        try:
            with get_session() as session:
                movimentacao = MovimentacaoEstoqueModel(
                    id_estoque=id_estoque,
                    id_produto=id_produto,
                    id_lote=id_lote,
                    tipo_movimentacao=tipo,
                    quantidade=quantidade,
                    data_movimentacao=datetime.now(),
                )
                session.add(movimentacao)
                session.flush()
                self._ajustar_saldo(session, id_estoque, id_produto, -quantidade)
                if id_lote is not None:
                    self._ajustar_saldo_lote(session, id_estoque, id_lote, -quantidade)
                session.flush()
                id_movimentacao = movimentacao.id_movimentacao
        except IntegrityError as exc:
            raise EstoqueError("Could not register stock exit.") from exc

        record = self.movimentacao_repo.get_by_id(id_movimentacao)
        if record is None:
            raise EstoqueError("Movement not found after insert.")
        return MovimentacaoEstoqueReadSchema.model_validate(record)

    def registrar_estorno_saida(
        self,
        *,
        id_estoque: int,
        id_produto: int,
        id_lote: int | None,
        quantidade: Decimal,
    ) -> MovimentacaoEstoqueReadSchema:
        """Reverses a previous activity/simple exit by restoring balance (ajuste)."""
        if quantidade <= 0:
            raise EstoqueError("Reversal quantity must be positive.")
        try:
            with get_session() as session:
                movimentacao = MovimentacaoEstoqueModel(
                    id_estoque=id_estoque,
                    id_produto=id_produto,
                    id_lote=id_lote,
                    tipo_movimentacao=MovementType.AJUSTE.value,
                    quantidade=quantidade,
                    data_movimentacao=datetime.now(),
                )
                session.add(movimentacao)
                session.flush()
                self._ajustar_saldo(session, id_estoque, id_produto, quantidade)
                if id_lote is not None:
                    self._ajustar_saldo_lote(session, id_estoque, id_lote, quantidade)
                session.flush()
                id_movimentacao = movimentacao.id_movimentacao
        except IntegrityError as exc:
            raise EstoqueError("Could not reverse stock exit.") from exc

        record = self.movimentacao_repo.get_by_id(id_movimentacao)
        if record is None:
            raise EstoqueError("Movement not found after insert.")
        return MovimentacaoEstoqueReadSchema.model_validate(record)

    # ------------------------------------------------------------------
    # Recebimento de compra (entrada real)
    # ------------------------------------------------------------------

    def registrar_recebimento(
            self, payload: RecebimentoCompraCreateSchema
        ) -> RecebimentoCompraReadSchema:
            """Confirma o recebimento físico de um item de compra, dando entrada no estoque.

            O lote, quando informado (código presente na nota/etiqueta do fornecedor),
            é criado se ainda não existir, ou reaproveitado se já tiver sido cadastrado
            por um recebimento anterior do mesmo produto (ex: entrega parcial).
            """
            item = self.order_item_repo.get_by_id(payload.id_item_pedido)
            if item is None:
                raise EstoqueError("Item de pedido não encontrado.")

            compras = self.purchase_repo.list(filters={"id_pedido": item.id_pedido})
            if not compras:
                raise EstoqueError("Nenhuma compra registrada para este pedido ainda.")
            compra = compras[0]

            ja_recebido = self.recebimento_repo.total_recebido_por_item(payload.id_item_pedido)
            if ja_recebido + payload.quantidade_recebida > item.quantidade:
                raise EstoqueError("Quantidade recebida excede o que foi pedido para este item.")

            data_recebimento = payload.data_recebimento or datetime.now()

            try:
                with get_session() as session:
                    id_lote = payload.id_lote
                    if id_lote is not None:
                        lote_existente = session.get(LoteModel, id_lote)
                        if lote_existente is None:
                            raise EstoqueError("Lote selecionado nao encontrado.")
                        if lote_existente.id_produto != item.id_produto:
                            raise EstoqueError(
                                "O lote selecionado pertence a outro produto."
                            )
                    else:
                        lote = self._create_lote_auto(
                            session,
                            id_produto=item.id_produto,
                            tipo_origem=LotOriginType.COMPRA,
                            validade=payload.validade_lote,
                            quantidade_inicial=payload.quantidade_recebida,
                        )
                        id_lote = lote.id_lote

                    movimentacao = MovimentacaoEstoqueModel(
                        id_estoque=payload.id_estoque,
                        id_produto=item.id_produto,
                        id_lote=id_lote,
                        tipo_movimentacao=MovementType.ENTRADA_COMPRA.value,
                        quantidade=payload.quantidade_recebida,
                        data_movimentacao=data_recebimento,
                    )
                    session.add(movimentacao)
                    session.flush()

                    # Legacy link kept for FK compatibility; recebimento_compra is canonical.
                    session.add(
                        EntradaEstoqueModel(
                            id_compra=compra.id_compra,
                            id_movimentacao=movimentacao.id_movimentacao,
                        )
                    )

                    recebimento = RecebimentoCompraModel(
                        id_item_pedido=payload.id_item_pedido,
                        id_estoque=payload.id_estoque,
                        id_movimentacao=movimentacao.id_movimentacao,
                        quantidade_recebida=payload.quantidade_recebida,
                        data_recebimento=data_recebimento,
                    )
                    session.add(recebimento)

                    self._ajustar_saldo(
                        session, payload.id_estoque, item.id_produto, payload.quantidade_recebida
                    )
                    if id_lote is not None:
                        self._ajustar_saldo_lote(
                            session,
                            payload.id_estoque,
                            id_lote,
                            payload.quantidade_recebida,
                        )

                    session.flush()
                    id_recebimento = recebimento.id_recebimento
            except IntegrityError as exc:
                raise EstoqueError(
                    "Não foi possível registrar o recebimento. Verifique os dados informados."
                ) from exc

            self._atualizar_status_pedido(item.id_pedido)

            record = self.recebimento_repo.get_by_id(id_recebimento)
            if record is None:
                raise EstoqueError("Recebimento não encontrado após o cadastro.")
            return RecebimentoCompraReadSchema.model_validate(record)

    def _atualizar_status_pedido(self, id_pedido: int) -> None:
        """Recalcula o status do pedido com base no total recebido de cada item."""
        itens = self.order_item_repo.list(filters={"id_pedido": id_pedido})
        if not itens:
            return

        totalmente_atendido = True
        algo_recebido = False
        for item in itens:
            recebido = self.recebimento_repo.total_recebido_por_item(item.id_item)
            if recebido > 0:
                algo_recebido = True
            if recebido < item.quantidade:
                totalmente_atendido = False

        if totalmente_atendido:
            novo_status = OrderStatus.ATENDIDO
        elif algo_recebido:
            novo_status = OrderStatus.PARCIALMENTE_ATENDIDO
        else:
            return

        self.order_repo.update(id_pedido, {"status": novo_status})

    def list_recebimentos_by_item(self, id_item_pedido: int) -> list[RecebimentoCompraReadSchema]:
        return [
            RecebimentoCompraReadSchema.model_validate(item) 
            for item in self.recebimento_repo.list_by_item_pedido(id_item_pedido)
        ]
    
    def list_recebimentos_by_estoque(
        self,
        id_estoque: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RecebimentoCompraReadSchema]:
        return [
            RecebimentoCompraReadSchema.model_validate(item)
            for item in self.recebimento_repo.list_by_estoque(id_estoque, limit, offset)
        ]

    # ------------------------------------------------------------------
    # Entrada por colheita
    # ------------------------------------------------------------------
    
    def registrar_entrada_colheita(
            self, payload: EntradaColheitaCreateSchema
        ) -> EntradaColheitaReadSchema:
            """Registra a entrada no estoque de um produto colhido, criando o lote de origem."""
            data_entrada = payload.data_entrada or datetime.now()

            try:
                with get_session() as session:
                    lote = self._create_lote_auto(
                        session,
                        id_produto=payload.id_produto,
                        id_colheita=payload.id_colheita,
                        tipo_origem=LotOriginType.COLHEITA,
                        validade=payload.validade_lote,
                        qualidade=payload.qualidade_lote,
                        quantidade_inicial=payload.quantidade,
                    )

                    movimentacao = MovimentacaoEstoqueModel(
                        id_estoque=payload.id_estoque,
                        id_produto=payload.id_produto,
                        id_lote=lote.id_lote,
                        tipo_movimentacao=MovementType.ENTRADA_COLHEITA.value,
                        quantidade=payload.quantidade,
                        data_movimentacao=data_entrada,
                    )
                    session.add(movimentacao)
                    session.flush()

                    entrada_colheita = EntradaColheitaEstoqueModel(
                        id_colheita=payload.id_colheita,
                        id_movimentacao=movimentacao.id_movimentacao,
                    )
                    session.add(entrada_colheita)

                    self._ajustar_saldo(
                        session, payload.id_estoque, payload.id_produto, payload.quantidade
                    )
                    self._ajustar_saldo_lote(
                        session, payload.id_estoque, lote.id_lote, payload.quantidade
                    )

                    session.flush()
                    resultado = EntradaColheitaReadSchema(
                        id_entrada_colheita=entrada_colheita.id_entrada_colheita,
                        id_colheita=entrada_colheita.id_colheita,
                        id_movimentacao=entrada_colheita.id_movimentacao,
                    )
            except IntegrityError as exc:
                raise EstoqueError(
                    "Não foi possível registrar a entrada. Verifique os dados informados."
                ) from exc

            return resultado
    
    # ------------------------------------------------------------------
    # Saída por venda
    # ------------------------------------------------------------------

    @contextmanager
    def _connection(self, conn=None):
        """Reutiliza uma conexao/transacao existente (para participar da mesma
        transacao de quem chamou, ex. ComercialService.registrar_venda) ou abre
        uma nova (uso standalone)."""
        if conn is not None:
            yield conn
        else:
            with pg_connector.pool.begin() as new_conn:
                yield new_conn

    def registrar_saida_venda(
        self,
        id_estoque: int,
        id_produto: int,
        id_item_venda: int,
        quantidade: Decimal,
        id_lote: int | None = None,
        conn=None,
    ) -> MovimentacaoEstoqueReadSchema:
        """Registra a saída de estoque motivada por uma venda.

        Usa SQL puro (em vez do padrão ORM do restante do módulo) para poder
        participar, via `conn`, da mesma transação de
        `ComercialService.registrar_venda`: se a baixa falhar, a venda inteira
        (e a conta a receber) é revertida junto.
        """
        sql_check = text(
            "select quantidade_atual from saldo_estoque "
            "where id_estoque = :id_estoque and id_produto = :id_produto for update"
        )
        sql_insert_mov = text(
            """
            insert into movimentacao_estoque
                (id_estoque, id_produto, id_lote, tipo_movimentacao, quantidade, data_movimentacao)
            values
                (:id_estoque, :id_produto, :id_lote, 'saida_venda', :quantidade, :data_movimentacao)
            returning id_movimentacao, id_estoque, id_produto, id_lote, tipo_movimentacao,
                      quantidade, data_movimentacao
            """
        )
        sql_insert_saida = text(
            "insert into saida_venda_estoque (id_movimentacao, id_item_venda) "
            "values (:id_movimentacao, :id_item_venda)"
        )
        sql_update_saldo = text(
            "update saldo_estoque set quantidade_atual = quantidade_atual - :quantidade "
            "where id_estoque = :id_estoque and id_produto = :id_produto"
        )
        sql_update_saldo_lote = text(
            "update saldo_lote set quantidade_atual = quantidade_atual - :quantidade "
            "where id_estoque = :id_estoque and id_lote = :id_lote"
        )

        try:
            with self._connection(conn) as c:
                saldo_atual = c.execute(
                    sql_check, {"id_estoque": id_estoque, "id_produto": id_produto}
                ).scalar_one_or_none()
                if saldo_atual is None or saldo_atual < quantidade:
                    raise EstoqueError("Saldo insuficiente para registrar a saída.")

                row = c.execute(
                    sql_insert_mov,
                    {
                        "id_estoque": id_estoque,
                        "id_produto": id_produto,
                        "id_lote": id_lote,
                        "quantidade": quantidade,
                        "data_movimentacao": datetime.now(),
                    },
                ).one()
                c.execute(
                    sql_insert_saida,
                    {"id_movimentacao": row.id_movimentacao, "id_item_venda": id_item_venda},
                )
                c.execute(
                    sql_update_saldo,
                    {"quantidade": quantidade, "id_estoque": id_estoque, "id_produto": id_produto},
                )
                if id_lote is not None:
                    c.execute(
                        sql_update_saldo_lote,
                        {
                            "quantidade": quantidade,
                            "id_estoque": id_estoque,
                            "id_lote": id_lote,
                        },
                    )
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível registrar a saída. Verifique os dados informados."
            ) from exc

        return MovimentacaoEstoqueReadSchema(**row._mapping)

    # ------------------------------------------------------------------
    # Saída por atividade agrícola (consumo)
    # ------------------------------------------------------------------

    def registrar_saida_atividade(
        self,
        id_estoque: int,
        id_produto: int,
        id_atividade: int,
        quantidade: Decimal,
        id_lote: int | None = None,
    ) -> MovimentacaoEstoqueReadSchema:
        """Registra a saída de estoque motivada pelo consumo em uma atividade agrícola."""
        if id_lote is not None:
            self._assert_saldo_lote(id_estoque, id_lote, quantidade)
        else:
            saldo = self.saldo_repo.get_by_estoque_produto(id_estoque, id_produto)
            if saldo is None or saldo.quantidade_atual < quantidade:
                raise EstoqueError("Insufficient stock balance for activity exit.")

        try:
            with get_session() as session:
                movimentacao = MovimentacaoEstoqueModel(
                    id_estoque=id_estoque,
                    id_produto=id_produto,
                    id_lote=id_lote,
                    tipo_movimentacao=MovementType.SAIDA_ATIVIDADE.value,
                    quantidade=quantidade,
                    data_movimentacao=datetime.now(),
                )
                session.add(movimentacao)
                session.flush()

                session.add(
                    SaidaEstoqueModel(
                        id_movimentacao=movimentacao.id_movimentacao,
                        id_atividade=id_atividade,
                    )
                )

                self._ajustar_saldo(session, id_estoque, id_produto, -quantidade)
                if id_lote is not None:
                    self._ajustar_saldo_lote(session, id_estoque, id_lote, -quantidade)
                session.flush()
                id_movimentacao = movimentacao.id_movimentacao
        except IntegrityError as exc:
            raise EstoqueError(
                "Could not register activity exit. Check the provided data."
            ) from exc

        record = self.movimentacao_repo.get_by_id(id_movimentacao)
        if record is None:
            raise EstoqueError("Movement not found after insert.")
        return MovimentacaoEstoqueReadSchema.model_validate(record)

    # ------------------------------------------------------------------
    # Saldo (helper interno)
    # ------------------------------------------------------------------

    def _assert_saldo_lote(
        self, id_estoque: int, id_lote: int, quantidade: Decimal
    ) -> None:
        saldo = self.saldo_lote_repo.get_by_estoque_lote(id_estoque, id_lote)
        if saldo is None:
            raise EstoqueError("Lot balance not found at the selected warehouse.")
        disponivel = Decimal(str(saldo.quantidade_atual)) - Decimal(
            str(saldo.quantidade_reservada)
        )
        if disponivel < quantidade:
            raise EstoqueError("Insufficient lot balance for the requested quantity.")

    @staticmethod
    def _ajustar_saldo(session: Session, id_estoque: int, id_produto: int, delta: Decimal) -> None:
        """Incrementa (delta positivo) ou decrementa (delta negativo) o saldo, criando se necessário."""
        saldo = (
            session.query(SaldoEstoqueModel)
            .filter_by(id_estoque=id_estoque, id_produto=id_produto)
            .with_for_update()
            .first()
        )
        if saldo is None:
            session.add(
                SaldoEstoqueModel(
                    id_estoque=id_estoque,
                    id_produto=id_produto,
                    quantidade_atual=delta,
                )
            )
        else:
            saldo.quantidade_atual += delta

    @staticmethod
    def _ajustar_saldo_lote(
        session: Session, id_estoque: int, id_lote: int, delta: Decimal
    ) -> None:
        saldo = (
            session.query(SaldoLoteModel)
            .filter_by(id_estoque=id_estoque, id_lote=id_lote)
            .with_for_update()
            .first()
        )
        if saldo is None:
            if delta < 0:
                raise EstoqueError("Lot balance not found for exit.")
            session.add(
                SaldoLoteModel(
                    id_estoque=id_estoque,
                    id_lote=id_lote,
                    quantidade_atual=delta,
                    quantidade_reservada=Decimal("0"),
                )
            )
        else:
            novo = Decimal(str(saldo.quantidade_atual)) + delta
            if novo < 0:
                raise EstoqueError("Lot balance would become negative.")
            saldo.quantidade_atual = novo

    # ------------------------------------------------------------------
    # Consultas de saldo
    # ------------------------------------------------------------------

    def get_saldo(self, id_estoque: int, id_produto: int) -> SaldoEstoqueReadSchema | None:
        record = self.saldo_repo.get_by_estoque_produto(id_estoque, id_produto)

        if record is None:
            return None
        
        return SaldoEstoqueReadSchema.model_validate(record)

    def list_saldo_by_estoque(self, id_estoque: int) -> list[SaldoEstoqueReadSchema]:
        return [
            SaldoEstoqueReadSchema.model_validate(item)
            for item in self.saldo_repo.list_by_estoque(id_estoque)
        ]

    def list_saldo_by_produto(self, id_produto: int) -> list[SaldoEstoqueReadSchema]:
        return [
            SaldoEstoqueReadSchema.model_validate(item) 
            for item in self.saldo_repo.list_by_produto(id_produto)
        ]

    def list_saldo_by_estoque_com_produto(
        self,
        id_estoque: int,
    ) -> list[SaldoEstoqueReadSchema]:
        result = []

        for saldo, produto_nome in self.saldo_repo.list_by_estoque_com_produto(id_estoque):
            schema = SaldoEstoqueReadSchema.model_validate(saldo)
            schema.produto_nome = produto_nome
            result.append(schema)

        return result
    
    # ------------------------------------------------------------------
    # Consultas de movimentação
    # ------------------------------------------------------------------

    def list_movimentacoes_by_estoque(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueReadSchema]:
        return [
            MovimentacaoEstoqueReadSchema.model_validate(item)
            for item in self.movimentacao_repo.list_by_estoque(id_estoque, limit, offset)
        ]

    def list_movimentacoes_by_lote(
        self, id_lote: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueReadSchema]:
        return [
            MovimentacaoEstoqueReadSchema.model_validate(item)
            for item in self.movimentacao_repo.list_by_lote(id_lote, limit, offset)
        ]

    def list_movimentacoes_by_estoque_com_produto(
        self,
        id_estoque: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovimentacaoEstoqueReadSchema]:
        result = []

        for mov, produto_nome, lote_codigo in self.movimentacao_repo.list_by_estoque_com_produto(
            id_estoque,
            limit,
            offset,
        ):
            schema = MovimentacaoEstoqueReadSchema.model_validate(mov)
            schema.produto_nome = produto_nome
            schema.lote_codigo = lote_codigo
            result.append(schema)

        return result
    
    def list_movimentacoes_by_periodo(
        self,
        id_estoque: int,
        data_inicio: datetime,
        data_fim: datetime,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovimentacaoEstoqueReadSchema]:
        return [
            MovimentacaoEstoqueReadSchema.model_validate(item)
            for item in self.movimentacao_repo.list_by_estoque_periodo(
                id_estoque,
                data_inicio,
                data_fim,
                limit,
                offset,
            )
        ]
    
    # ------------------------------------------------------------------
    # Lotes
    # ------------------------------------------------------------------

    def create_lote(self, payload: LoteCreateSchema) -> LoteReadSchema:
        try:
            with get_session() as session:
                lote = self._create_lote_auto(
                    session,
                    id_produto=payload.id_produto,
                    id_colheita=payload.id_colheita,
                    tipo_origem=payload.tipo_origem,
                    validade=payload.validade,
                    qualidade=payload.qualidade,
                    quantidade_inicial=payload.quantidade_inicial,
                    status=payload.status,
                )
                id_lote = lote.id_lote
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível criar o lote. Verifique os dados informados."
            ) from exc
        record = self.get_lote_com_produto(id_lote)
        if record is None:
            raise EstoqueError("Lote nao encontrado apos o cadastro.")
        return record
    
    def get_lote(self, id_lote: int) -> LoteReadSchema | None:
        record = self.lote_repo.get_by_id(id_lote)

        if record is None:
            return None

        return LoteReadSchema.model_validate(record)

    def list_lotes(self) -> list[LoteReadSchema]:
        return [
            LoteReadSchema.model_validate(item) for item in self.lote_repo.list()
        ]

    def update_lote(self, id_lote: int, payload: LoteUpdateSchema) -> LoteReadSchema | None:
        try:
            record = self.lote_repo.update(id_lote, payload.model_dump(exclude_unset=True))
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível atualizar o lote. Verifique os dados informados."
            ) from exc

        if record is None:
            return None

        return LoteReadSchema.model_validate(record)
        
    def delete_lote(self, id_lote: int) -> bool:
        if self.movimentacao_repo.exists_by_lote(id_lote):
            raise EstoqueError("Não é possível excluir um lote que possui movimentações.")
        
        if self.certificacao_repo.exists_by_lote(id_lote):
            raise EstoqueError("Não é possível excluir um lote que possui certificações.")
        
        return self.lote_repo.delete(id_lote)

    def get_lote_by_codigo(self, codigo: str) -> LoteReadSchema | None:
        record = self.lote_repo.get_by_codigo(codigo)

        if record is None:
            return None

        return LoteReadSchema.model_validate(record)

    def list_lotes_com_produto(self, limit: int = 50, offset: int = 0) -> list[LoteReadSchema]:
        result = []

        for lote, produto_nome in self.lote_repo.list_com_produto(limit, offset):
            schema = LoteReadSchema.model_validate(lote)
            schema.produto_nome = produto_nome
            result.append(schema)

        return result

    def get_lote_com_produto(self, id_lote: int) -> LoteReadSchema | None:
        record = self.lote_repo.get_com_produto(id_lote)

        if record is None:
            return None

        lote, produto_nome = record

        schema = LoteReadSchema.model_validate(lote)
        schema.produto_nome = produto_nome
        return schema
    
    def list_lotes_proximos_vencimento(self, dias: int) -> list[LoteReadSchema]:
        return [
            LoteReadSchema.model_validate(item)
            for item in self.lote_repo.list_proximos_vencimento(dias)
        ]
    
    def list_lotes_vencidos(self) -> list[LoteReadSchema]:
        return [
            LoteReadSchema.model_validate(item)
            for item in self.lote_repo.list_vencidos()
        ]
    
    # ------------------------------------------------------------------
    # Estoques
    # ------------------------------------------------------------------

    def create_estoque(self, payload: EstoqueCreateSchema) -> EstoqueReadSchema:
        try:
            record = self.estoque_repo.create(payload.model_dump())
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível criar o estoque. Verifique os dados informados."
            ) from exc
        return EstoqueReadSchema.model_validate(record)
        
    def get_estoque(self, id_estoque: int) -> EstoqueReadSchema | None:
        result = self.estoque_repo.get_com_local(id_estoque)

        if result is None:
            return None

        estoque, local_descricao = result

        schema = EstoqueReadSchema.model_validate(estoque)
        schema.local_descricao = local_descricao

        return schema

    def list_estoques(self) -> list[EstoqueReadSchema]:
        return [
            EstoqueReadSchema.model_validate(item) for item in self.estoque_repo.list()
        ]

    def delete_estoque(self, id_estoque: int) -> bool:
        if self.saldo_repo.exists_by_estoque(id_estoque):
            raise EstoqueError(
                "Não é possível excluir um estoque que possui saldo."
            )

        if self.movimentacao_repo.exists_by_estoque(id_estoque):
            raise EstoqueError(
                "Não é possível excluir um estoque que possui movimentações."
            )
        
        return self.estoque_repo.delete(id_estoque)

    def list_estoques_com_local(self) -> list[EstoqueReadSchema]:
        result = []
        for estoque, local_descricao in self.estoque_repo.list_com_local():
            schema = EstoqueReadSchema.model_validate(estoque)
            schema.local_descricao = local_descricao
            result.append(schema)
        return result
    
    def list_estoques_by_local(self, id_local: int) -> list[EstoqueReadSchema]:
        return [
            EstoqueReadSchema.model_validate(item)
            for item in self.estoque_repo.list_by_local(id_local)
        ]
    
    # ------------------------------------------------------------------
    # Locais de armazenamento
    # ------------------------------------------------------------------

    def create_local(self, payload: LocalArmazenamentoCreateSchema) -> LocalArmazenamentoReadSchema:
        try:
            record = self.local_repo.create(payload.model_dump())
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível criar o local. Verifique os dados informados."
            ) from exc
        return LocalArmazenamentoReadSchema.model_validate(record)

    def get_local(self, id_local: int) -> LocalArmazenamentoReadSchema | None:
        record = self.local_repo.get_by_id(id_local)

        if record is None:
            return None

        return LocalArmazenamentoReadSchema.model_validate(record)

    def list_locais(self) -> list[LocalArmazenamentoReadSchema]:
        return [
            LocalArmazenamentoReadSchema.model_validate(item) for item in self.local_repo.list()
        ]

    def update_local(
        self, id_local: int, payload: LocalArmazenamentoUpdateSchema
    ) -> LocalArmazenamentoReadSchema | None:
        try:
            record = self.local_repo.update(id_local, payload.model_dump(exclude_unset=True))
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível atualizar o local. Verifique os dados informados."
            ) from exc

        if record is None:
            return None

        return LocalArmazenamentoReadSchema.model_validate(record)
    
    def delete_local(self, id_local: int) -> bool:
        if self.estoque_repo.exists_by_local(id_local):
            raise EstoqueError(
                "Não é possível excluir um local que possui estoques."
            )
        
        return self.local_repo.delete(id_local)

    # ------------------------------------------------------------------
    # Certificações
    # ------------------------------------------------------------------

    def create_certificacao(self, payload: CertificacaoLoteCreateSchema) -> CertificacaoLoteReadSchema:
        existente = self.certificacao_repo.get_by_certificacao_lote(
            payload.id_certificacao,
            payload.id_lote,
        )

        if existente is not None:
            raise EstoqueError(
                "Esta certificação já está vinculada a este lote."
            )
        
        try:
            record = self.certificacao_repo.create(payload.model_dump())
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível vincular a certificação ao lote. Verifique os dados informados."
            ) from exc
        return CertificacaoLoteReadSchema.model_validate(record)

    def get_certificacao(self, id_certificacao_lote: int) -> CertificacaoLoteReadSchema | None:
        record = self.certificacao_repo.get_by_id(id_certificacao_lote)

        if record is None:
            return None

        return CertificacaoLoteReadSchema.model_validate(record)

    def list_certificacoes(self, limit: int = 50, offset: int = 0) -> list[CertificacaoLoteReadSchema]:
        return [
            CertificacaoLoteReadSchema.model_validate(item)
            for item in self.certificacao_repo.list_paginado(limit, offset)
        ]

    def update_certificacao(
        self, id_certificacao_lote: int, payload: CertificacaoLoteUpdateSchema
    ) -> CertificacaoLoteReadSchema | None:
        try:
            record = self.certificacao_repo.update(
                id_certificacao_lote, payload.model_dump(exclude_unset=True)
            )
        except IntegrityError as exc:
            raise EstoqueError(
                "Não foi possível atualizar a certificação. Verifique os dados informados."
            ) from exc

        if record is None:
            return None

        return CertificacaoLoteReadSchema.model_validate(record)

    def delete_certificacao(self, id_certificacao_lote: int) -> bool:
        return self.certificacao_repo.delete(id_certificacao_lote)

    def list_certificacoes_by_lote(
        self,
        id_lote: int,
    ) -> list[CertificacaoLoteReadSchema]:
        result = []
        for cert, lote_codigo, certificacao_nome in self.certificacao_repo.list_by_lote_com_detalhes(id_lote):
            schema = CertificacaoLoteReadSchema.model_validate(cert)
            schema.lote_codigo = lote_codigo
            schema.certificacao_nome = certificacao_nome
            result.append(schema)
        return result

    # ------------------------------------------------------------------
    # Lookups (para preencher comboboxes/selects no frontend)
    # ------------------------------------------------------------------

    def list_produto_options(self) -> list[ProdutoOptionSchema]:
        return [
            ProdutoOptionSchema(id_produto=id_produto, nome=nome)
            for id_produto, nome in self.lookup_repo.list_produtos()
        ]

    def list_colheita_options(self) -> list[ColheitaOptionSchema]:
        return [
            ColheitaOptionSchema(id_colheita=id_colheita, label=label)
            for id_colheita, label in self.lookup_repo.list_colheitas()
        ]

    def list_local_options(self) -> list[LocalArmazenamentoOptionSchema]:
        return [
            LocalArmazenamentoOptionSchema(id_local=id_local, descricao=descricao)
            for id_local, descricao in self.lookup_repo.list_locais()
        ]

    def list_estoque_options(self) -> list[EstoqueOptionSchema]:
        return [
            EstoqueOptionSchema(id_estoque=id_estoque, descricao=descricao)
            for id_estoque, descricao in self.lookup_repo.list_estoques()
        ]

    def list_lote_options(self) -> list[LoteOptionSchema]:
        return [
            LoteOptionSchema(
                id_lote=id_lote,
                codigo_lote=codigo_lote,
                id_produto=id_produto,
                produto_nome=produto_nome,
            )
            for id_lote, codigo_lote, id_produto, produto_nome in self.lookup_repo.list_lotes()
        ]

    def list_certificacao_options(self) -> list[CertificacaoOptionSchema]:
        return [
            CertificacaoOptionSchema(id_certificacao=id_certificacao, nome=nome)
            for id_certificacao, nome in self.lookup_repo.list_certificacoes()
        ]

    def list_item_pedido_options(self) -> list[ItemPedidoOptionSchema]:
        return [
            ItemPedidoOptionSchema(
                id_item_pedido=id_item,
                id_produto=id_produto,
                descricao=descricao,
            )
            for id_item, id_produto, descricao in self.lookup_repo.list_itens_pedido_pendentes()
        ]