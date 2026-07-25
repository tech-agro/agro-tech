"""Recebe requisições da interface para o domínio estoque."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

from app.estoque.errors import EstoqueError
from app.estoque.schemas.certificacao_lote import (
    CertificacaoLoteCreateSchema,
    CertificacaoLoteReadSchema,
    CertificacaoLoteUpdateSchema,
)
from app.estoque.schemas.estoque import EstoqueCreateSchema, EstoqueReadSchema
from app.estoque.schemas.local_armazenamento import (
    LocalArmazenamentoCreateSchema,
    LocalArmazenamentoReadSchema,
    LocalArmazenamentoUpdateSchema,
)
from app.estoque.schemas.lote import LoteCreateSchema, LoteReadSchema, LoteUpdateSchema
from app.estoque.schemas.movimentacao_estoque import MovimentacaoEstoqueReadSchema
from app.estoque.schemas.recebimento_compra import (
    RecebimentoCompraCreateSchema,
    RecebimentoCompraReadSchema,
)
from app.estoque.schemas.saldo_estoque import SaldoEstoqueReadSchema
from app.estoque.schemas.entrada_colheita_estoque import EntradaColheitaCreateSchema, EntradaColheitaReadSchema
from app.estoque.schemas.lookups import (
    CertificacaoOptionSchema,
    ColheitaOptionSchema,
    EstoqueOptionSchema,
    ItemPedidoOptionSchema,
    LocalArmazenamentoOptionSchema,
    LoteOptionSchema,
    ProdutoOptionSchema,
)
from app.estoque.service import EstoqueService


class EstoqueController:
    """Adaptador entre interface e service."""

    def __init__(self, service: EstoqueService | None = None) -> None:
        self.service = service or EstoqueService()
        self.router = APIRouter(prefix="/estoque", tags=["estoque"])
        self._register_routes()

    @staticmethod
    def _map_error(exc: EstoqueError) -> HTTPException:
        return HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    def _register_routes(self) -> None:
        # --- Lotes ---
        self.router.get("/lotes", response_model=list[LoteReadSchema])(self.list_lotes)
        self.router.get(
            "/lotes/vencidos", response_model=list[LoteReadSchema]
        )(self.list_lotes_vencidos)
        self.router.get(
            "/lotes/proximos-vencimento", response_model=list[LoteReadSchema]
        )(self.list_lotes_proximos_vencimento)
        self.router.get(
            "/lotes/codigo/{codigo}", response_model=LoteReadSchema
        )(self.get_lote_by_codigo)
        self.router.get("/lotes/{id_lote}", response_model=LoteReadSchema)(self.get_lote)
        self.router.patch("/lotes/{id_lote}", response_model=LoteReadSchema)(self.update_lote)
        self.router.delete("/lotes/{id_lote}", status_code=status.HTTP_204_NO_CONTENT)(
            self.delete_lote
        )

        # --- Locais de armazenamento ---
        self.router.post(
            "/locais", response_model=LocalArmazenamentoReadSchema
        )(self.create_local)
        self.router.get(
            "/locais", response_model=list[LocalArmazenamentoReadSchema]
        )(self.list_locais)
        self.router.get(
            "/locais/{id_local}", response_model=LocalArmazenamentoReadSchema
        )(self.get_local)
        self.router.patch(
            "/locais/{id_local}", response_model=LocalArmazenamentoReadSchema
        )(self.update_local)
        self.router.delete("/locais/{id_local}", status_code=status.HTTP_204_NO_CONTENT)(
            self.delete_local
        )

        # --- Estoques ---
        self.router.post("/estoques", response_model=EstoqueReadSchema)(self.create_estoque)
        self.router.get("/estoques", response_model=list[EstoqueReadSchema])(
            self.list_estoques
        )
        self.router.get(
            "/estoques/local/{id_local}", response_model=list[EstoqueReadSchema]
        )(self.list_estoques_by_local)
        self.router.get(
            "/estoques/{id_estoque}", response_model=EstoqueReadSchema
        )(self.get_estoque)
        self.router.delete(
            "/estoques/{id_estoque}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_estoque)

        # --- Certificações de lote ---
        self.router.post(
            "/certificacoes", response_model=CertificacaoLoteReadSchema
        )(self.create_certificacao)
        self.router.get(
            "/certificacoes", response_model=list[CertificacaoLoteReadSchema]
        )(self.list_certificacoes)
        self.router.get(
            "/certificacoes/lote/{id_lote}", response_model=list[CertificacaoLoteReadSchema]
        )(self.list_certificacoes_by_lote)
        self.router.get(
            "/certificacoes/{id_certificacao_lote}", response_model=CertificacaoLoteReadSchema
        )(self.get_certificacao)
        self.router.patch(
            "/certificacoes/{id_certificacao_lote}", response_model=CertificacaoLoteReadSchema
        )(self.update_certificacao)
        self.router.delete(
            "/certificacoes/{id_certificacao_lote}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_certificacao)

        # --- Saldo ---
        self.router.get(
            "/saldo/estoque/{id_estoque}", response_model=list[SaldoEstoqueReadSchema]
        )(self.list_saldo_by_estoque)
        self.router.get(
            "/saldo/produto/{id_produto}", response_model=list[SaldoEstoqueReadSchema]
        )(self.list_saldo_by_produto)
        self.router.get(
            "/saldo/{id_estoque}/{id_produto}", response_model=SaldoEstoqueReadSchema
        )(self.get_saldo)

        # --- Movimentações ---
        self.router.get(
            "/movimentacoes/estoque/{id_estoque}",
            response_model=list[MovimentacaoEstoqueReadSchema],
        )(self.list_movimentacoes_by_estoque)
        self.router.get(
            "/movimentacoes/lote/{id_lote}",
            response_model=list[MovimentacaoEstoqueReadSchema],
        )(self.list_movimentacoes_by_lote)
        self.router.get(
            "/movimentacoes/estoque/{id_estoque}/periodo",
            response_model=list[MovimentacaoEstoqueReadSchema],
        )(self.list_movimentacoes_by_periodo)

        # --- Recebimento de compra ---
        self.router.post(
            "/recebimentos", response_model=RecebimentoCompraReadSchema
        )(self.registrar_recebimento)
        self.router.get(
            "/recebimentos/item/{id_item_pedido}",
            response_model=list[RecebimentoCompraReadSchema],
        )(self.list_recebimentos_by_item)
        self.router.get(
            "/recebimentos/estoque/{id_estoque}",
            response_model=list[RecebimentoCompraReadSchema],
        )(self.list_recebimentos_by_estoque)

        # --- Entrada por colheita ---
        self.router.post(
            "/entradas-colheita", response_model=EntradaColheitaReadSchema
        )(self.registrar_entrada_colheita)

        # --- Lookups (para preencher comboboxes/selects no frontend) ---
        self.router.get(
            "/lookups/produtos", response_model=list[ProdutoOptionSchema]
        )(self.list_produto_options)
        self.router.get(
            "/lookups/colheitas", response_model=list[ColheitaOptionSchema]
        )(self.list_colheita_options)
        self.router.get(
            "/lookups/locais", response_model=list[LocalArmazenamentoOptionSchema]
        )(self.list_local_options)
        self.router.get(
            "/lookups/estoques", response_model=list[EstoqueOptionSchema]
        )(self.list_estoque_options)
        self.router.get(
            "/lookups/lotes", response_model=list[LoteOptionSchema]
        )(self.list_lote_options)
        self.router.get(
            "/lookups/certificacoes", response_model=list[CertificacaoOptionSchema]
        )(self.list_certificacao_options)
        self.router.get(
            "/lookups/itens-pedido", response_model=list[ItemPedidoOptionSchema]
        )(self.list_item_pedido_options)

    # ------------------------------------------------------------------
    # Lotes
    # ------------------------------------------------------------------

    def list_lotes(self, limit: int = 50, offset: int = 0) -> list[LoteReadSchema]:
        return self.service.list_lotes_com_produto(limit, offset)
    
    def list_lotes_vencidos(self) -> list[LoteReadSchema]:
        return self.service.list_lotes_vencidos()

    def list_lotes_proximos_vencimento(self, dias: int = 30) -> list[LoteReadSchema]:
        return self.service.list_lotes_proximos_vencimento(dias)

    def get_lote_by_codigo(self, codigo: str) -> LoteReadSchema:
        lote = self.service.get_lote_by_codigo(codigo)
        if lote is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote não encontrado")
        return lote

    def get_lote(self, id_lote: int) -> LoteReadSchema:
        lote = self.service.get_lote_com_produto(id_lote)
        if lote is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote não encontrado")
        return lote

    def update_lote(self, id_lote: int, payload: LoteUpdateSchema) -> LoteReadSchema:
        try:
            lote = self.service.update_lote(id_lote, payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc
        if lote is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote não encontrado")
        return lote

    def delete_lote(self, id_lote: int) -> None:
        try:
            ok = self.service.delete_lote(id_lote)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote não encontrado")

    # ------------------------------------------------------------------
    # Locais de armazenamento
    # ------------------------------------------------------------------

    def create_local(
        self, payload: LocalArmazenamentoCreateSchema
    ) -> LocalArmazenamentoReadSchema:
        try:
            return self.service.create_local(payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc

    def list_locais(self) -> list[LocalArmazenamentoReadSchema]:
        return self.service.list_locais()

    def get_local(self, id_local: int) -> LocalArmazenamentoReadSchema:
        local = self.service.get_local(id_local)
        if local is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Local não encontrado")
        return local

    def update_local(
        self, id_local: int, payload: LocalArmazenamentoUpdateSchema
    ) -> LocalArmazenamentoReadSchema:
        try:
            local = self.service.update_local(id_local, payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc
        if local is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Local não encontrado")
        return local

    def delete_local(self, id_local: int) -> None:
        try:
            ok = self.service.delete_local(id_local)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Local não encontrado")

    # ------------------------------------------------------------------
    # Estoques
    # ------------------------------------------------------------------

    def create_estoque(self, payload: EstoqueCreateSchema) -> EstoqueReadSchema:
        try:
            return self.service.create_estoque(payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc

    def list_estoques(self) -> list[EstoqueReadSchema]:
        return self.service.list_estoques_com_local()

    def list_estoques_by_local(self, id_local: int) -> list[EstoqueReadSchema]:
        return self.service.list_estoques_by_local(id_local)

    def get_estoque(self, id_estoque: int) -> EstoqueReadSchema:
        estoque = self.service.get_estoque(id_estoque)
        if estoque is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Estoque não encontrado")
        return estoque

    def delete_estoque(self, id_estoque: int) -> None:
        try:
            ok = self.service.delete_estoque(id_estoque)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Estoque não encontrado")

    # ------------------------------------------------------------------
    # Certificações
    # ------------------------------------------------------------------

    def create_certificacao(
        self, payload: CertificacaoLoteCreateSchema
    ) -> CertificacaoLoteReadSchema:
        try:
            return self.service.create_certificacao(payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc

    def list_certificacoes(self, limit: int = 50, offset: int = 0) -> list[CertificacaoLoteReadSchema]:
        return self.service.list_certificacoes(limit, offset)

    def list_certificacoes_by_lote(self, id_lote: int) -> list[CertificacaoLoteReadSchema]:
        return self.service.list_certificacoes_by_lote(id_lote)

    def get_certificacao(self, id_certificacao_lote: int) -> CertificacaoLoteReadSchema:
        cert = self.service.get_certificacao(id_certificacao_lote)
        if cert is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificação não encontrada")
        return cert

    def update_certificacao(
        self, id_certificacao_lote: int, payload: CertificacaoLoteUpdateSchema
    ) -> CertificacaoLoteReadSchema:
        try:
            cert = self.service.update_certificacao(id_certificacao_lote, payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc
        if cert is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificação não encontrada")
        return cert

    def delete_certificacao(self, id_certificacao_lote: int) -> None:
        if not self.service.delete_certificacao(id_certificacao_lote):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificação não encontrada")

    # ------------------------------------------------------------------
    # Saldo
    # ------------------------------------------------------------------

    def get_saldo(self, id_estoque: int, id_produto: int) -> SaldoEstoqueReadSchema:
        saldo = self.service.get_saldo(id_estoque, id_produto)
        if saldo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Saldo não encontrado")
        return saldo

    def list_saldo_by_estoque(self, id_estoque: int) -> list[SaldoEstoqueReadSchema]:
        return self.service.list_saldo_by_estoque_com_produto(id_estoque)

    def list_saldo_by_produto(self, id_produto: int) -> list[SaldoEstoqueReadSchema]:
        return self.service.list_saldo_by_produto(id_produto)

    # ------------------------------------------------------------------
    # Movimentações
    # ------------------------------------------------------------------

    def list_movimentacoes_by_estoque(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueReadSchema]:
        return self.service.list_movimentacoes_by_estoque_com_produto(id_estoque, limit, offset)

    def list_movimentacoes_by_lote(
        self, id_lote: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueReadSchema]:
        return self.service.list_movimentacoes_by_lote(id_lote, limit, offset)

    def list_movimentacoes_by_periodo(
        self,
        id_estoque: int,
        data_inicio: datetime,
        data_fim: datetime,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovimentacaoEstoqueReadSchema]:
        return self.service.list_movimentacoes_by_periodo(
            id_estoque, data_inicio, data_fim, limit, offset
        )

    # ------------------------------------------------------------------
    # Recebimento de compra
    # ------------------------------------------------------------------

    def registrar_recebimento(
        self, payload: RecebimentoCompraCreateSchema
    ) -> RecebimentoCompraReadSchema:
        try:
            return self.service.registrar_recebimento(payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc

    def list_recebimentos_by_item(
        self, id_item_pedido: int
    ) -> list[RecebimentoCompraReadSchema]:
        return self.service.list_recebimentos_by_item(id_item_pedido)

    def list_recebimentos_by_estoque(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[RecebimentoCompraReadSchema]:
        return self.service.list_recebimentos_by_estoque(id_estoque, limit, offset)
    
    # ------------------------------------------------------------------
    # Entrada por colheita
    # ------------------------------------------------------------------

    def registrar_entrada_colheita(
        self, payload: EntradaColheitaCreateSchema
    ) -> EntradaColheitaReadSchema:
        try:
            return self.service.registrar_entrada_colheita(payload)
        except EstoqueError as exc:
            raise self._map_error(exc) from exc

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def list_produto_options(self) -> list[ProdutoOptionSchema]:
        return self.service.list_produto_options()

    def list_colheita_options(self) -> list[ColheitaOptionSchema]:
        return self.service.list_colheita_options()

    def list_local_options(self) -> list[LocalArmazenamentoOptionSchema]:
        return self.service.list_local_options()

    def list_estoque_options(self) -> list[EstoqueOptionSchema]:
        return self.service.list_estoque_options()

    def list_lote_options(self) -> list[LoteOptionSchema]:
        return self.service.list_lote_options()

    def list_certificacao_options(self) -> list[CertificacaoOptionSchema]:
        return self.service.list_certificacao_options()

    def list_item_pedido_options(self) -> list[ItemPedidoOptionSchema]:
        return self.service.list_item_pedido_options()


estoque_controller = EstoqueController()
router = estoque_controller.router