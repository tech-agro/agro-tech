"""HTTP adapter for the financeiro domain."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.financeiro.enum import StatusContaPagarEnum, StatusContaReceberEnum
from app.financeiro.errors import FinanceiroError
from app.financeiro.lookups import (
    CompraOptionSchema,
    ContaPagarOptionSchema,
    ContaReceberOptionSchema,
    DespesaLogisticaOptionSchema,
    FormaPagamentoOptionSchema,
    ManutencaoOptionSchema,
    VendaOptionSchema,
)
from app.financeiro.schemas import (
    ConfiguracaoFinanceiraReadSchema,
    ConfiguracaoFinanceiraUpdateSchema,
    ContaPagarCreateSchema,
    ContaPagarReadSchema,
    ContaPagarUpdateSchema,
    ContaReceberCreateSchema,
    ContaReceberReadSchema,
    ContaReceberUpdateSchema,
    FluxoCaixaReadSchema,
    PagamentoCreateSchema,
    PagamentoReadSchema,
    PagamentoUpdateSchema,
    RecebimentoCreateSchema,
    RecebimentoReadSchema,
    RecebimentoUpdateSchema,
)
from app.financeiro.service import FinanceiroService


class FinanceiroController:
    """Exposes ContaPagar/Pagamento, ContaReceber/Recebimento, FluxoCaixa,
    ConfiguracaoFinanceira and lookups do módulo financeiro."""

    def __init__(self, service: FinanceiroService | None = None) -> None:
        self.service = service or FinanceiroService()
        self.router = APIRouter(prefix="/financeiro", tags=["financeiro"])
        self._register_routes()

    @staticmethod
    def _map_error(exc: FinanceiroError) -> HTTPException:
        return HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    def _register_routes(self) -> None:
        # --- Lookups ---
        self.router.get(
            "/lookups/compras", response_model=list[CompraOptionSchema]
        )(self.list_compra_options)
        self.router.get(
            "/lookups/manutencoes", response_model=list[ManutencaoOptionSchema]
        )(self.list_manutencao_options)
        self.router.get(
            "/lookups/despesas-logisticas",
            response_model=list[DespesaLogisticaOptionSchema],
        )(self.list_despesa_logistica_options)
        self.router.get(
            "/lookups/vendas", response_model=list[VendaOptionSchema]
        )(self.list_venda_options)
        self.router.get(
            "/lookups/contas-pagar", response_model=list[ContaPagarOptionSchema]
        )(self.list_conta_pagar_options)
        self.router.get(
            "/lookups/contas-receber", response_model=list[ContaReceberOptionSchema]
        )(self.list_conta_receber_options)
        self.router.get(
            "/lookups/formas-pagamento", response_model=list[FormaPagamentoOptionSchema]
        )(self.list_forma_pagamento_options)

        # --- Contas a pagar ---
        self.router.post(
            "/contas-pagar", response_model=ContaPagarReadSchema
        )(self.create_conta_pagar)
        self.router.get(
            "/contas-pagar", response_model=list[ContaPagarReadSchema]
        )(self.list_contas_pagar)
        self.router.get(
            "/contas-pagar/{id_conta_pagar}", response_model=ContaPagarReadSchema
        )(self.get_conta_pagar)
        self.router.patch(
            "/contas-pagar/{id_conta_pagar}", response_model=ContaPagarReadSchema
        )(self.update_conta_pagar)
        self.router.delete(
            "/contas-pagar/{id_conta_pagar}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_conta_pagar)

        # --- Pagamentos (aninhados sob conta a pagar + coleção geral) ---
        self.router.post(
            "/pagamentos", response_model=PagamentoReadSchema
        )(self.create_pagamento)
        self.router.get(
            "/pagamentos", response_model=list[PagamentoReadSchema]
        )(self.list_pagamentos)
        self.router.get(
            "/contas-pagar/{id_conta_pagar}/pagamentos",
            response_model=list[PagamentoReadSchema],
        )(self.list_pagamentos_por_conta)
        self.router.get(
            "/pagamentos/{id_pagamento}", response_model=PagamentoReadSchema
        )(self.get_pagamento)
        self.router.patch(
            "/pagamentos/{id_pagamento}", response_model=PagamentoReadSchema
        )(self.update_pagamento)
        self.router.delete(
            "/pagamentos/{id_pagamento}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_pagamento)

        # --- Contas a receber ---
        self.router.post(
            "/contas-receber", response_model=ContaReceberReadSchema
        )(self.create_conta_receber)
        self.router.get(
            "/contas-receber", response_model=list[ContaReceberReadSchema]
        )(self.list_contas_receber)
        self.router.get(
            "/contas-receber/{id_conta_receber}", response_model=ContaReceberReadSchema
        )(self.get_conta_receber)
        self.router.patch(
            "/contas-receber/{id_conta_receber}", response_model=ContaReceberReadSchema
        )(self.update_conta_receber)
        self.router.delete(
            "/contas-receber/{id_conta_receber}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_conta_receber)

        # --- Recebimentos (aninhados sob conta a receber + coleção geral) ---
        self.router.post(
            "/recebimentos", response_model=RecebimentoReadSchema
        )(self.create_recebimento)
        self.router.get(
            "/recebimentos", response_model=list[RecebimentoReadSchema]
        )(self.list_recebimentos)
        self.router.get(
            "/contas-receber/{id_conta_receber}/recebimentos",
            response_model=list[RecebimentoReadSchema],
        )(self.list_recebimentos_por_conta)
        self.router.get(
            "/recebimentos/{id_recebimento}", response_model=RecebimentoReadSchema
        )(self.get_recebimento)
        self.router.patch(
            "/recebimentos/{id_recebimento}", response_model=RecebimentoReadSchema
        )(self.update_recebimento)
        self.router.delete(
            "/recebimentos/{id_recebimento}", status_code=status.HTTP_204_NO_CONTENT
        )(self.delete_recebimento)

        # --- Fluxo de caixa (somente leitura) ---
        self.router.get(
            "/fluxo-caixa", response_model=list[FluxoCaixaReadSchema]
        )(self.list_fluxo_por_periodo)
        self.router.get(
            "/fluxo-caixa/resumo", response_model=dict[str, str]
        )(self.resumo_fluxo_por_periodo)
        self.router.get(
            "/contas-pagar/{id_conta_pagar}/fluxo-caixa",
            response_model=list[FluxoCaixaReadSchema],
        )(self.list_fluxo_por_conta_pagar)
        self.router.get(
            "/contas-receber/{id_conta_receber}/fluxo-caixa",
            response_model=list[FluxoCaixaReadSchema],
        )(self.list_fluxo_por_conta_receber)

        # --- Configuração financeira (singleton) ---
        self.router.get(
            "/configuracao", response_model=ConfiguracaoFinanceiraReadSchema
        )(self.get_configuracao_financeira)
        self.router.patch(
            "/configuracao", response_model=ConfiguracaoFinanceiraReadSchema
        )(self.update_configuracao_financeira)

    # ============================================================
    # LOOKUPS
    # ============================================================

    def list_compra_options(self) -> list[CompraOptionSchema]:
        return self.service.list_compra_options()

    def list_manutencao_options(self) -> list[ManutencaoOptionSchema]:
        return self.service.list_manutencao_options()

    def list_despesa_logistica_options(self) -> list[DespesaLogisticaOptionSchema]:
        return self.service.list_despesa_logistica_options()

    def list_venda_options(self) -> list[VendaOptionSchema]:
        return self.service.list_venda_options()

    def list_conta_pagar_options(self) -> list[ContaPagarOptionSchema]:
        return self.service.list_conta_pagar_options()

    def list_conta_receber_options(self) -> list[ContaReceberOptionSchema]:
        return self.service.list_conta_receber_options()

    def list_forma_pagamento_options(self) -> list[FormaPagamentoOptionSchema]:
        return self.service.list_forma_pagamento_options()

    # ============================================================
    # CONTAS A PAGAR
    # ============================================================

    def create_conta_pagar(self, payload: ContaPagarCreateSchema) -> ContaPagarReadSchema:
        try:
            return self.service.create_conta_pagar(payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def list_contas_pagar(
        self,
        status_: StatusContaPagarEnum | None = Query(default=None, alias="status"),
        vencendo_em: int | None = Query(default=None),
        vencidas: bool = Query(default=False),
        limit: int = Query(default=50),
        offset: int = Query(default=0),
    ) -> list[ContaPagarReadSchema]:
        try:
            return self.service.list_contas_pagar(
                status=status_,
                vencendo_em=vencendo_em,
                vencidas=vencidas,
                limit=limit,
                offset=offset,
            )
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def get_conta_pagar(self, id_conta_pagar: int) -> ContaPagarReadSchema:
        conta = self.service.get_conta_pagar(id_conta_pagar)
        if conta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta a pagar não encontrado(a)")
        return conta

    def update_conta_pagar(
        self, id_conta_pagar: int, payload: ContaPagarUpdateSchema
    ) -> ContaPagarReadSchema:
        try:
            conta = self.service.update_conta_pagar(id_conta_pagar, payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if conta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta a pagar não encontrado(a)")
        return conta

    def delete_conta_pagar(self, id_conta_pagar: int) -> None:
        try:
            ok = self.service.delete_conta_pagar(id_conta_pagar)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta a pagar não encontrado(a)")

    # ============================================================
    # PAGAMENTOS
    # ============================================================

    def create_pagamento(self, payload: PagamentoCreateSchema) -> PagamentoReadSchema:
        try:
            return self.service.create_pagamento(payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def list_pagamentos(
        self,
        limit: int = Query(default=50),
        offset: int = Query(default=0),
    ) -> list[PagamentoReadSchema]:
        return self.service.list_pagamentos(limit=limit, offset=offset)

    def list_pagamentos_por_conta(self, id_conta_pagar: int) -> list[PagamentoReadSchema]:
        try:
            return self.service.list_pagamentos_por_conta(id_conta_pagar)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def get_pagamento(self, id_pagamento: int) -> PagamentoReadSchema:
        pagamento = self.service.get_pagamento(id_pagamento)
        if pagamento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pagamento não encontrado(a)")
        return pagamento

    def update_pagamento(
        self, id_pagamento: int, payload: PagamentoUpdateSchema
    ) -> PagamentoReadSchema:
        try:
            pagamento = self.service.update_pagamento(id_pagamento, payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if pagamento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pagamento não encontrado(a)")
        return pagamento

    def delete_pagamento(self, id_pagamento: int) -> None:
        try:
            ok = self.service.delete_pagamento(id_pagamento)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pagamento não encontrado(a)")

    # ============================================================
    # CONTAS A RECEBER
    # ============================================================

    def create_conta_receber(
        self, payload: ContaReceberCreateSchema
    ) -> ContaReceberReadSchema:
        try:
            return self.service.create_conta_receber(payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def list_contas_receber(
        self,
        status_: StatusContaReceberEnum | None = Query(default=None, alias="status"),
        vencendo_em: int | None = Query(default=None),
        vencidas: bool = Query(default=False),
        limit: int = Query(default=50),
        offset: int = Query(default=0),
    ) -> list[ContaReceberReadSchema]:
        try:
            return self.service.list_contas_receber(
                status=status_,
                vencendo_em=vencendo_em,
                vencidas=vencidas,
                limit=limit,
                offset=offset,
            )
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def get_conta_receber(self, id_conta_receber: int) -> ContaReceberReadSchema:
        conta = self.service.get_conta_receber(id_conta_receber)
        if conta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta a receber não encontrado(a)")
        return conta

    def update_conta_receber(
        self, id_conta_receber: int, payload: ContaReceberUpdateSchema
    ) -> ContaReceberReadSchema:
        try:
            conta = self.service.update_conta_receber(id_conta_receber, payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if conta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta a receber não encontrado(a)")
        return conta

    def delete_conta_receber(self, id_conta_receber: int) -> None:
        try:
            ok = self.service.delete_conta_receber(id_conta_receber)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conta a receber não encontrado(a)")

    # ============================================================
    # RECEBIMENTOS
    # ============================================================

    def create_recebimento(self, payload: RecebimentoCreateSchema) -> RecebimentoReadSchema:
        try:
            return self.service.create_recebimento(payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def list_recebimentos(
        self,
        limit: int = Query(default=50),
        offset: int = Query(default=0),
    ) -> list[RecebimentoReadSchema]:
        return self.service.list_recebimentos(limit=limit, offset=offset)

    def list_recebimentos_por_conta(
        self, id_conta_receber: int
    ) -> list[RecebimentoReadSchema]:
        try:
            return self.service.list_recebimentos_por_conta(id_conta_receber)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def get_recebimento(self, id_recebimento: int) -> RecebimentoReadSchema:
        recebimento = self.service.get_recebimento(id_recebimento)
        if recebimento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Recebimento não encontrado(a)")
        return recebimento

    def update_recebimento(
        self, id_recebimento: int, payload: RecebimentoUpdateSchema
    ) -> RecebimentoReadSchema:
        try:
            recebimento = self.service.update_recebimento(id_recebimento, payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if recebimento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Recebimento não encontrado(a)")
        return recebimento

    def delete_recebimento(self, id_recebimento: int) -> None:
        try:
            ok = self.service.delete_recebimento(id_recebimento)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        if not ok:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Recebimento não encontrado(a)")

    # ============================================================
    # FLUXO DE CAIXA
    # ============================================================

    def list_fluxo_por_periodo(
        self,
        data_inicio: date = Query(...),
        data_fim: date = Query(...),
        tipo: str | None = Query(default=None),
        limit: int = Query(default=50),
        offset: int = Query(default=0),
    ) -> list[FluxoCaixaReadSchema]:
        try:
            return self.service.list_fluxo_por_periodo(
                data_inicio=data_inicio,
                data_fim=data_fim,
                tipo=tipo,
                limit=limit,
                offset=offset,
            )
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def resumo_fluxo_por_periodo(
        self,
        data_inicio: date = Query(...),
        data_fim: date = Query(...),
    ) -> dict[str, str]:
        try:
            totais = self.service.resumo_fluxo_por_periodo(data_inicio, data_fim)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc
        return {tipo: str(valor) for tipo, valor in totais.items()}

    def list_fluxo_por_conta_pagar(self, id_conta_pagar: int) -> list[FluxoCaixaReadSchema]:
        try:
            return self.service.list_fluxo_por_conta_pagar(id_conta_pagar)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    def list_fluxo_por_conta_receber(
        self, id_conta_receber: int
    ) -> list[FluxoCaixaReadSchema]:
        try:
            return self.service.list_fluxo_por_conta_receber(id_conta_receber)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc

    # ============================================================
    # CONFIGURAÇÃO FINANCEIRA
    # ============================================================

    def get_configuracao_financeira(self) -> ConfiguracaoFinanceiraReadSchema:
        config = self.service.get_configuracao_financeira()
        if config is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Configuração financeira não encontrado(a)"
            )
        return config

    def update_configuracao_financeira(
        self, payload: ConfiguracaoFinanceiraUpdateSchema
    ) -> ConfiguracaoFinanceiraReadSchema:
        try:
            return self.service.update_configuracao_financeira(payload)
        except FinanceiroError as exc:
            raise self._map_error(exc) from exc


financeiro_controller = FinanceiroController()
router = financeiro_controller.router