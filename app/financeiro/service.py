"""Regras de negocio do dominio financeiro."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.financeiro.enum import (
    StatusContaPagarEnum,
    StatusContaReceberEnum,
)
from app.financeiro.errors import FinanceiroError
from app.financeiro.models import FluxoCaixaModel
from app.financeiro.repository import (
    ConfiguracaoFinanceiraRepository,
    ContaPagarRepository,
    ContaReceberRepository,
    FinanceiroLookupRepository,
    FluxoCaixaRepository,
    PagamentoRepository,
    RecebimentoRepository,
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
from app.financeiro.lookups import (
    CompraOptionSchema,
    ContaPagarOptionSchema,
    ContaReceberOptionSchema,
    DespesaLogisticaOptionSchema,
    FormaPagamentoOptionSchema,
    ManutencaoOptionSchema,
    VendaOptionSchema,
)

_STATUS_CONTA_PAGAR_ABERTOS = (
    StatusContaPagarEnum.ABERTA,
    StatusContaPagarEnum.PARCIALMENTE_PAGA,
)

_STATUS_CONTA_RECEBER_ABERTOS = (
    StatusContaReceberEnum.ABERTA,
    StatusContaReceberEnum.PARCIALMENTE_RECEBIDA,
)


class FinanceiroService:
    """Casos de uso do módulo financeiro."""

    def __init__(
        self,
        conta_pagar_repo: ContaPagarRepository | None = None,
        pagamento_repo: PagamentoRepository | None = None,
        conta_receber_repo: ContaReceberRepository | None = None,
        recebimento_repo: RecebimentoRepository | None = None,
        fluxo_repo: FluxoCaixaRepository | None = None,
        configuracao_repo: ConfiguracaoFinanceiraRepository | None = None,
        lookup_repo: FinanceiroLookupRepository | None = None,
    ) -> None:
        self.conta_pagar_repo = conta_pagar_repo or ContaPagarRepository()
        self.pagamento_repo = pagamento_repo or PagamentoRepository()
        self.conta_receber_repo = conta_receber_repo or ContaReceberRepository()
        self.recebimento_repo = recebimento_repo or RecebimentoRepository()
        self.fluxo_repo = fluxo_repo or FluxoCaixaRepository()
        self.configuracao_repo = (
            configuracao_repo or ConfiguracaoFinanceiraRepository()
        )
        self.lookup_repo = lookup_repo or FinanceiroLookupRepository()

    # ============================================================
    # HOOKS DE INTEGRAÇÃO
    # ============================================================
    # Chamados por outros módulos (compras, manutenção, operação
    # logística, vendas) no momento em que uma aquisição/venda é
    # confirmada e deve gerar automaticamente uma conta a
    # pagar/receber. São idempotentes: se a conta já existir para a
    # origem informada, retornam a existente em vez de lançar erro —
    # o módulo chamador não precisa controlar se já dispensou o hook
    # antes (ex.: reprocessamento, retry).

    def create_conta_pagar_from_compra(
        self,
        id_compra: int,
        valor: Decimal,
        vencimento: date | None = None,
    ) -> ContaPagarReadSchema:
        existente = self.conta_pagar_repo.get_by_compra(id_compra)

        if existente is not None:
            loaded = self._load_conta_pagar_read(existente.id_conta_pagar)
            assert loaded is not None
            return loaded

        return self.create_conta_pagar(
            ContaPagarCreateSchema(
                id_compra=id_compra,
                valor=valor,
                vencimento=vencimento,
            )
        )

    def create_conta_pagar_from_manutencao(
        self,
        id_manutencao: int,
        valor: Decimal,
        vencimento: date | None = None,
    ) -> ContaPagarReadSchema:
        existente = self.conta_pagar_repo.get_by_manutencao(id_manutencao)

        if existente is not None:
            loaded = self._load_conta_pagar_read(existente.id_conta_pagar)
            assert loaded is not None
            return loaded

        return self.create_conta_pagar(
            ContaPagarCreateSchema(
                id_manutencao=id_manutencao,
                valor=valor,
                vencimento=vencimento,
            )
        )

    def create_conta_pagar_from_despesa_logistica(
        self,
        id_despesa_logistica: int,
        valor: Decimal,
        vencimento: date | None = None,
    ) -> ContaPagarReadSchema:
        existente = self.conta_pagar_repo.get_by_despesa_logistica(id_despesa_logistica)

        if existente is not None:
            loaded = self._load_conta_pagar_read(existente.id_conta_pagar)
            assert loaded is not None
            return loaded

        return self.create_conta_pagar(
            ContaPagarCreateSchema(
                id_despesa_logistica=id_despesa_logistica,
                valor=valor,
                vencimento=vencimento,
            )
        )

    def create_conta_receber_from_venda(
        self,
        id_venda: int,
        valor: Decimal,
        vencimento: date | None = None,
    ) -> ContaReceberReadSchema:
        existente = self.conta_receber_repo.get_by_venda(id_venda)

        if existente is not None:
            loaded = self._load_conta_receber_read(existente.id_conta_receber)
            assert loaded is not None
            return loaded

        return self.create_conta_receber(
            ContaReceberCreateSchema(
                id_venda=id_venda,
                valor=valor,
                vencimento=vencimento,
            )
        )

    @staticmethod
    def _to_conta_pagar_read(
        conta,
        origem,
        compra_valor,
        manutencao_tipo,
        manutencao_custo,
        manutencao_data,
        despesa_descricao,
        despesa_tipo,
        despesa_data,
        valor_pago,
        saldo,
    ) -> ContaPagarReadSchema:

        data = ContaPagarReadSchema.model_validate(conta).model_dump()

        data.update(
            origem=origem,
            compra_valor=compra_valor,
            manutencao_tipo=manutencao_tipo,
            manutencao_custo=manutencao_custo,
            manutencao_data=manutencao_data,
            despesa_descricao=despesa_descricao,
            despesa_tipo=despesa_tipo,
            despesa_data=despesa_data,
            valor_pago=valor_pago,
            saldo=saldo,
        )

        return ContaPagarReadSchema.model_validate(data)

    @staticmethod
    def _to_conta_receber_read(
        conta,
        valor_venda,
        data_venda,
        valor_recebido,
        saldo,
    ) -> ContaReceberReadSchema:

        data = ContaReceberReadSchema.model_validate(conta).model_dump()

        data.update(
            valor_venda=valor_venda,
            data_venda=data_venda,
            valor_recebido=valor_recebido,
            saldo=saldo,
        )

        return ContaReceberReadSchema.model_validate(data)

    @staticmethod
    def _to_pagamento_read(
        pagamento,
        vencimento,
        status,
        saldo,
    ) -> PagamentoReadSchema:

        data = PagamentoReadSchema.model_validate(pagamento).model_dump()

        data.update(
            vencimento=vencimento,
            status=status,
            saldo=saldo,
        )

        return PagamentoReadSchema.model_validate(data)

    @staticmethod
    def _to_recebimento_read(
        recebimento,
        vencimento,
        status,
        saldo,
    ) -> RecebimentoReadSchema:

        data = RecebimentoReadSchema.model_validate(recebimento).model_dump()

        data.update(
            vencimento=vencimento,
            status=status,
            saldo=saldo,
        )

        return RecebimentoReadSchema.model_validate(data)

    @staticmethod
    def _to_fluxo_read(
        fluxo: FluxoCaixaModel,
    ) -> FluxoCaixaReadSchema:

        data = FluxoCaixaReadSchema.model_validate(fluxo).model_dump()

        if fluxo.id_conta_pagar is not None:
            data["origem"] = "CONTA_PAGAR"
            data["descricao_origem"] = (
                f"Conta a pagar #{fluxo.id_conta_pagar}"
            )

        elif fluxo.id_conta_receber is not None:
            data["origem"] = "CONTA_RECEBER"
            data["descricao_origem"] = (
                f"Conta a receber #{fluxo.id_conta_receber}"
            )

        return FluxoCaixaReadSchema.model_validate(data)

    @staticmethod
    def _validar_filtros_vencimento(
        status,
        vencendo_em: int | None,
        vencidas: bool,
        status_abertos: tuple,
    ) -> None:
        if vencendo_em is not None and vencidas:
            raise FinanceiroError(
                "Não é possível combinar 'vencendo_em' (a vencer) com "
                "'vencidas' (já vencidas) na mesma consulta."
            )

        if vencendo_em is not None and vencendo_em < 0:
            raise FinanceiroError(
                "'vencendo_em' deve ser um número de dias maior ou "
                "igual a zero."
            )

        if (
            (vencendo_em is not None or vencidas)
            and status is not None
            and status not in status_abertos
        ):
            raise FinanceiroError(
                "O filtro de status informado é incompatível com "
                "'vencendo_em'/'vencidas', pois esses filtros só "
                "consideram contas em aberto ou parcialmente pagas/recebidas."
            )

    # ============================================================
    # CONTAS A PAGAR
    # ============================================================

    def _load_conta_pagar_read(
        self,
        id_conta_pagar: int,
    ) -> ContaPagarReadSchema | None:
        loaded = self.conta_pagar_repo.get_com_detalhes(id_conta_pagar)

        if loaded is None:
            return None

        (
            conta,
            origem,
            compra_valor,
            manutencao_tipo,
            manutencao_custo,
            manutencao_data,
            despesa_descricao,
            despesa_tipo,
            despesa_data,
            valor_pago,
            saldo,
        ) = loaded

        return self._to_conta_pagar_read(
            conta,
            origem,
            compra_valor,
            manutencao_tipo,
            manutencao_custo,
            manutencao_data,
            despesa_descricao,
            despesa_tipo,
            despesa_data,
            valor_pago,
            saldo,
        )


    def list_contas_pagar(
        self,
        status: StatusContaPagarEnum | None = None,
        vencendo_em: int | None = None,
        vencidas: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContaPagarReadSchema]:
        self._validar_filtros_vencimento(
            status, vencendo_em, vencidas, _STATUS_CONTA_PAGAR_ABERTOS
        )
        return [
            self._to_conta_pagar_read(
                conta,
                origem,
                compra_valor,
                manutencao_tipo,
                manutencao_custo,
                manutencao_data,
                despesa_descricao,
                despesa_tipo,
                despesa_data,
                valor_pago,
                saldo,
            )
            for (
                conta,
                origem,
                compra_valor,
                manutencao_tipo,
                manutencao_custo,
                manutencao_data,
                despesa_descricao,
                despesa_tipo,
                despesa_data,
                valor_pago,
                saldo,
            ) in self.conta_pagar_repo.list_com_detalhes(
                status=status,
                vencendo_em=vencendo_em,
                vencidas=vencidas,
                limit=limit,
                offset=offset,
            )
        ]


    def get_conta_pagar(
        self,
        id_conta_pagar: int,
    ) -> ContaPagarReadSchema | None:
        return self._load_conta_pagar_read(id_conta_pagar)


    def create_conta_pagar(
        self,
        payload: ContaPagarCreateSchema,
    ) -> ContaPagarReadSchema:

        data = payload.model_dump()

        data["status"] = StatusContaPagarEnum.ABERTA

        origem = [
            data.get("id_compra"),
            data.get("id_manutencao"),
            data.get("id_despesa_logistica"),
        ]

        if sum(valor is not None for valor in origem) > 1:
            raise FinanceiroError(
                "Uma conta a pagar só pode possuir uma origem."
            )

        if data.get("id_compra") is not None:
            if self.conta_pagar_repo.exists_by_compra(
                data["id_compra"]
            ):
                raise FinanceiroError(
                    "Já existe uma conta a pagar vinculada a esta compra."
                )

        if data.get("id_manutencao") is not None:
            if self.conta_pagar_repo.exists_by_manutencao(
                data["id_manutencao"]
            ):
                raise FinanceiroError(
                    "Já existe uma conta a pagar vinculada a esta manutenção."
                )

        if data.get("id_despesa_logistica") is not None:
            if self.conta_pagar_repo.exists_by_despesa_logistica(
                data["id_despesa_logistica"]
            ):
                raise FinanceiroError(
                    "Já existe uma conta a pagar vinculada a esta despesa."
                )

        try:
            record = self.conta_pagar_repo.create(data)

        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível criar a conta a pagar. "
                "Verifique os dados informados."
            ) from exc

        loaded = self._load_conta_pagar_read(
            record.id_conta_pagar
        )

        assert loaded is not None

        return loaded


    def update_conta_pagar(
        self,
        id_conta_pagar: int,
        payload: ContaPagarUpdateSchema,
    ) -> ContaPagarReadSchema | None:

        conta = self.conta_pagar_repo.get_by_id(id_conta_pagar)

        if conta is None:
            return None

        if self.pagamento_repo.exists_by_conta_pagar(
            id_conta_pagar
        ):
            campos = payload.model_dump(
                exclude_unset=True
            )

            if "valor" in campos:
                raise FinanceiroError(
                    "Não é permitido alterar o valor de uma conta "
                    "que já possui pagamentos."
                )

        try:
            record = self.conta_pagar_repo.update(
                id_conta_pagar,
                payload.model_dump(
                    exclude_unset=True
                ),
            )

        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível atualizar a conta a pagar."
            ) from exc

        if record is None:
            return None

        return self._load_conta_pagar_read(
            id_conta_pagar
        )


    def delete_conta_pagar(
        self,
        id_conta_pagar: int,
    ) -> bool:

        if self.conta_pagar_repo.get_by_id(id_conta_pagar) is None:
            return False

        if self.pagamento_repo.exists_by_conta_pagar(
            id_conta_pagar
        ):
            raise FinanceiroError(
                "Não é possível excluir uma conta a pagar "
                "que possui pagamentos registrados."
            )

        return self.conta_pagar_repo.delete(
            id_conta_pagar
        )


    # ============================================================
    # PAGAMENTOS
    # ============================================================

    def _load_pagamento_read(
        self,
        id_pagamento: int,
    ) -> PagamentoReadSchema | None:
        pagamento = self.pagamento_repo.get_by_id(id_pagamento)

        if pagamento is None:
            return None

        conta = self.conta_pagar_repo.get_by_id(pagamento.id_conta_pagar)

        vencimento = conta.vencimento if conta is not None else None
        status = conta.status if conta is not None else None
        saldo = None

        if conta is not None:
            total_pago = self.pagamento_repo.total_pago_por_conta(
                conta.id_conta_pagar
            )
            saldo = conta.valor - total_pago

        return self._to_pagamento_read(pagamento, vencimento, status, saldo)

    def _recalcular_status_conta_pagar(self, id_conta_pagar: int) -> None:
        conta = self.conta_pagar_repo.get_by_id(id_conta_pagar)

        if conta is None:
            return

        # Não sobrescreve status "finais"/manuais que não sejam de
        # progresso de pagamento.
        if conta.status in (
            StatusContaPagarEnum.CANCELADA,
            StatusContaPagarEnum.VENCIDA,
        ):
            return

        total_pago = self.pagamento_repo.total_pago_por_conta(id_conta_pagar)
        saldo = conta.valor - total_pago

        if saldo <= 0:
            novo_status = StatusContaPagarEnum.PAGA
        elif total_pago > 0:
            novo_status = StatusContaPagarEnum.PARCIALMENTE_PAGA
        else:
            novo_status = StatusContaPagarEnum.ABERTA

        if conta.status != novo_status:
            self.conta_pagar_repo.update(
                id_conta_pagar, {"status": novo_status}
            )

    def list_pagamentos(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PagamentoReadSchema]:
        return [
            self._to_pagamento_read(pagamento, vencimento, status, saldo)
            for (
                pagamento,
                vencimento,
                status,
                saldo,
            ) in self.pagamento_repo.list_com_detalhes(
                limit=limit, offset=offset
            )
        ]

    def list_pagamentos_por_conta(
        self,
        id_conta_pagar: int,
    ) -> list[PagamentoReadSchema]:
        conta = self.conta_pagar_repo.get_by_id(id_conta_pagar)

        if conta is None:
            raise FinanceiroError("Conta a pagar não encontrada.")

        total_pago = self.pagamento_repo.total_pago_por_conta(id_conta_pagar)
        saldo = conta.valor - total_pago

        return [
            self._to_pagamento_read(
                pagamento, conta.vencimento, conta.status, saldo
            )
            for pagamento in self.pagamento_repo.list_by_conta_pagar(
                id_conta_pagar
            )
        ]

    def get_pagamento(
        self,
        id_pagamento: int,
    ) -> PagamentoReadSchema | None:
        return self._load_pagamento_read(id_pagamento)

    def create_pagamento(
        self,
        payload: PagamentoCreateSchema,
    ) -> PagamentoReadSchema:
        conta = self.conta_pagar_repo.get_by_id(payload.id_conta_pagar)

        if conta is None:
            raise FinanceiroError("Conta a pagar não encontrada.")

        if conta.status == StatusContaPagarEnum.CANCELADA:
            raise FinanceiroError(
                "Não é possível registrar pagamento para uma conta cancelada."
            )

        if conta.status == StatusContaPagarEnum.PAGA:
            raise FinanceiroError("Esta conta a pagar já está quitada.")

        total_pago_atual = self.pagamento_repo.total_pago_por_conta(
            conta.id_conta_pagar
        )
        saldo = conta.valor - total_pago_atual

        if payload.valor_pago > saldo:
            raise FinanceiroError(
                f"Valor pago (R$ {payload.valor_pago}) excede o saldo "
                f"devedor da conta (R$ {saldo})."
            )

        try:
            pagamento = self.pagamento_repo.create(payload.model_dump())
        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível registrar o pagamento."
            ) from exc

        self._recalcular_status_conta_pagar(conta.id_conta_pagar)

        try:
            self.fluxo_repo.create(
                {
                    "id_conta_pagar": conta.id_conta_pagar,
                    "id_conta_receber": None,
                    "id_pagamento": pagamento.id_pagamento,
                    "id_recebimento": None,
                    "valor": payload.valor_pago,
                    "tipo": "SAIDA",
                    "data_movimento": payload.data_pagamento,
                }
            )
        except IntegrityError as exc:
            raise FinanceiroError(
                "Pagamento registrado, mas houve falha ao lançar no fluxo de caixa."
            ) from exc

        loaded = self._load_pagamento_read(pagamento.id_pagamento)

        assert loaded is not None

        return loaded

    def update_pagamento(
        self,
        id_pagamento: int,
        payload: PagamentoUpdateSchema,
    ) -> PagamentoReadSchema | None:
        pagamento = self.pagamento_repo.get_by_id(id_pagamento)

        if pagamento is None:
            return None

        try:
            self.pagamento_repo.update(
                id_pagamento, payload.model_dump(exclude_unset=True)
            )
        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível atualizar o pagamento."
            ) from exc

        return self._load_pagamento_read(id_pagamento)

    def delete_pagamento(
        self,
        id_pagamento: int,
    ) -> bool:
        pagamento = self.pagamento_repo.get_by_id(id_pagamento)

        if pagamento is None:
            return False

        id_conta_pagar = pagamento.id_conta_pagar

        fluxo = self.fluxo_repo.get_by_pagamento(id_pagamento)

        if fluxo is not None:
            try:
                self.fluxo_repo.delete(fluxo.id_fluxo)
            except IntegrityError as exc:
                raise FinanceiroError(
                    "Não foi possível remover o lançamento de fluxo de "
                    "caixa associado a este pagamento."
                ) from exc

        deletado = self.pagamento_repo.delete(id_pagamento)

        if deletado:
            self._recalcular_status_conta_pagar(id_conta_pagar)

        return deletado


    # ============================================================
    # CONTAS A RECEBER
    # ============================================================

    def _load_conta_receber_read(
        self,
        id_conta_receber: int,
    ) -> ContaReceberReadSchema | None:
        loaded = self.conta_receber_repo.get_com_detalhes(id_conta_receber)

        if loaded is None:
            return None

        (
            conta,
            valor_venda,
            data_venda,
            valor_recebido,
            saldo,
        ) = loaded

        return self._to_conta_receber_read(
            conta,
            valor_venda,
            data_venda,
            valor_recebido,
            saldo,
        )

    def list_contas_receber(
        self,
        status: StatusContaReceberEnum | None = None,
        vencendo_em: int | None = None,
        vencidas: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContaReceberReadSchema]:
        self._validar_filtros_vencimento(
            status, vencendo_em, vencidas, _STATUS_CONTA_RECEBER_ABERTOS
        )
        return [
            self._to_conta_receber_read(
                conta,
                valor_venda,
                data_venda,
                valor_recebido,
                saldo,
            )
            for (
                conta,
                valor_venda,
                data_venda,
                valor_recebido,
                saldo,
            ) in self.conta_receber_repo.list_com_detalhes(
                status=status,
                vencendo_em=vencendo_em,
                vencidas=vencidas,
                limit=limit,
                offset=offset,
            )
        ]

    def get_conta_receber(
        self,
        id_conta_receber: int,
    ) -> ContaReceberReadSchema | None:
        return self._load_conta_receber_read(id_conta_receber)

    def create_conta_receber(
        self,
        payload: ContaReceberCreateSchema,
    ) -> ContaReceberReadSchema:

        data = payload.model_dump()

        data["status"] = StatusContaReceberEnum.ABERTA

        if self.conta_receber_repo.exists_by_venda(data["id_venda"]):
            raise FinanceiroError(
                "Já existe uma conta a receber vinculada a esta venda."
            )

        try:
            record = self.conta_receber_repo.create(data)

        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível criar a conta a receber. "
                "Verifique os dados informados."
            ) from exc

        loaded = self._load_conta_receber_read(record.id_conta_receber)

        assert loaded is not None

        return loaded

    def update_conta_receber(
        self,
        id_conta_receber: int,
        payload: ContaReceberUpdateSchema,
    ) -> ContaReceberReadSchema | None:

        conta = self.conta_receber_repo.get_by_id(id_conta_receber)

        if conta is None:
            return None

        if self.recebimento_repo.exists_by_conta_receber(id_conta_receber):
            campos = payload.model_dump(exclude_unset=True)

            if "valor" in campos:
                raise FinanceiroError(
                    "Não é permitido alterar o valor de uma conta "
                    "que já possui recebimentos."
                )

        try:
            record = self.conta_receber_repo.update(
                id_conta_receber,
                payload.model_dump(exclude_unset=True),
            )

        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível atualizar a conta a receber."
            ) from exc

        if record is None:
            return None

        return self._load_conta_receber_read(id_conta_receber)

    def delete_conta_receber(
        self,
        id_conta_receber: int,
    ) -> bool:

        if self.conta_receber_repo.get_by_id(id_conta_receber) is None:
            return False

        if self.recebimento_repo.exists_by_conta_receber(id_conta_receber):
            raise FinanceiroError(
                "Não é possível excluir uma conta a receber "
                "que possui recebimentos registrados."
            )

        return self.conta_receber_repo.delete(id_conta_receber)


    # ============================================================
    # RECEBIMENTOS
    # ============================================================

    def _load_recebimento_read(
        self,
        id_recebimento: int,
    ) -> RecebimentoReadSchema | None:
        recebimento = self.recebimento_repo.get_by_id(id_recebimento)

        if recebimento is None:
            return None

        conta = self.conta_receber_repo.get_by_id(recebimento.id_conta_receber)

        vencimento = conta.vencimento if conta is not None else None
        status = conta.status if conta is not None else None
        saldo = None

        if conta is not None:
            total_recebido = self.recebimento_repo.total_recebido_por_conta(
                conta.id_conta_receber
            )
            saldo = conta.valor - total_recebido

        return self._to_recebimento_read(recebimento, vencimento, status, saldo)

    def _recalcular_status_conta_receber(self, id_conta_receber: int) -> None:
        conta = self.conta_receber_repo.get_by_id(id_conta_receber)

        if conta is None:
            return

        # Não sobrescreve status "finais"/manuais que não sejam de
        # progresso de recebimento.
        if conta.status in (
            StatusContaReceberEnum.CANCELADA,
            StatusContaReceberEnum.VENCIDA,
        ):
            return

        total_recebido = self.recebimento_repo.total_recebido_por_conta(
            id_conta_receber
        )
        saldo = conta.valor - total_recebido

        if saldo <= 0:
            novo_status = StatusContaReceberEnum.RECEBIDA
        elif total_recebido > 0:
            novo_status = StatusContaReceberEnum.PARCIALMENTE_RECEBIDA
        else:
            novo_status = StatusContaReceberEnum.ABERTA

        if conta.status != novo_status:
            self.conta_receber_repo.update(
                id_conta_receber, {"status": novo_status}
            )

    def list_recebimentos(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RecebimentoReadSchema]:
        return [
            self._to_recebimento_read(recebimento, vencimento, status, saldo)
            for (
                recebimento,
                vencimento,
                status,
                saldo,
            ) in self.recebimento_repo.list_com_detalhes(
                limit=limit, offset=offset
            )
        ]

    def list_recebimentos_por_conta(
        self,
        id_conta_receber: int,
    ) -> list[RecebimentoReadSchema]:
        conta = self.conta_receber_repo.get_by_id(id_conta_receber)

        if conta is None:
            raise FinanceiroError("Conta a receber não encontrada.")

        total_recebido = self.recebimento_repo.total_recebido_por_conta(
            id_conta_receber
        )
        saldo = conta.valor - total_recebido

        return [
            self._to_recebimento_read(
                recebimento, conta.vencimento, conta.status, saldo
            )
            for recebimento in self.recebimento_repo.list_by_conta_receber(
                id_conta_receber
            )
        ]

    def get_recebimento(
        self,
        id_recebimento: int,
    ) -> RecebimentoReadSchema | None:
        return self._load_recebimento_read(id_recebimento)

    def create_recebimento(
        self,
        payload: RecebimentoCreateSchema,
    ) -> RecebimentoReadSchema:
        conta = self.conta_receber_repo.get_by_id(payload.id_conta_receber)

        if conta is None:
            raise FinanceiroError("Conta a receber não encontrada.")

        if conta.status == StatusContaReceberEnum.CANCELADA:
            raise FinanceiroError(
                "Não é possível registrar recebimento para uma conta cancelada."
            )

        if conta.status == StatusContaReceberEnum.RECEBIDA:
            raise FinanceiroError("Esta conta a receber já está quitada.")

        total_recebido_atual = self.recebimento_repo.total_recebido_por_conta(
            conta.id_conta_receber
        )
        saldo = conta.valor - total_recebido_atual

        if payload.valor_recebido > saldo:
            raise FinanceiroError(
                f"Valor recebido (R$ {payload.valor_recebido}) excede o "
                f"saldo a receber da conta (R$ {saldo})."
            )

        try:
            recebimento = self.recebimento_repo.create(payload.model_dump())
        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível registrar o recebimento."
            ) from exc

        self._recalcular_status_conta_receber(conta.id_conta_receber)

        try:
            self.fluxo_repo.create(
                {
                    "id_conta_pagar": None,
                    "id_conta_receber": conta.id_conta_receber,
                    "id_pagamento": None,
                    "id_recebimento": recebimento.id_recebimento,
                    "valor": payload.valor_recebido,
                    "tipo": "ENTRADA",
                    "data_movimento": payload.data_recebimento,
                }
            )
        except IntegrityError as exc:
            raise FinanceiroError(
                "Recebimento registrado, mas houve falha ao lançar no fluxo de caixa."
            ) from exc

        loaded = self._load_recebimento_read(recebimento.id_recebimento)

        assert loaded is not None

        return loaded

    def update_recebimento(
        self,
        id_recebimento: int,
        payload: RecebimentoUpdateSchema,
    ) -> RecebimentoReadSchema | None:
        recebimento = self.recebimento_repo.get_by_id(id_recebimento)

        if recebimento is None:
            return None

        try:
            self.recebimento_repo.update(
                id_recebimento, payload.model_dump(exclude_unset=True)
            )
        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível atualizar o recebimento."
            ) from exc

        return self._load_recebimento_read(id_recebimento)

    def delete_recebimento(
        self,
        id_recebimento: int,
    ) -> bool:
        recebimento = self.recebimento_repo.get_by_id(id_recebimento)

        if recebimento is None:
            return False

        id_conta_receber = recebimento.id_conta_receber

        fluxo = self.fluxo_repo.get_by_recebimento(id_recebimento)

        if fluxo is not None:
            try:
                self.fluxo_repo.delete(fluxo.id_fluxo)
            except IntegrityError as exc:
                raise FinanceiroError(
                    "Não foi possível remover o lançamento de fluxo de "
                    "caixa associado a este recebimento."
                ) from exc

        deletado = self.recebimento_repo.delete(id_recebimento)

        if deletado:
            self._recalcular_status_conta_receber(id_conta_receber)

        return deletado


    # ============================================================
    # FLUXO DE CAIXA
    # ============================================================
    # Somente leitura pela API — os lançamentos são criados
    # automaticamente pelo service a partir de pagamentos e
    # recebimentos confirmados (ver create_pagamento/create_recebimento).

    def list_fluxo_por_periodo(
        self,
        data_inicio: date,
        data_fim: date,
        tipo: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FluxoCaixaReadSchema]:
        if data_inicio > data_fim:
            raise FinanceiroError(
                "'data_inicio' não pode ser posterior a 'data_fim'."
            )

        return [
            self._to_fluxo_read(fluxo)
            for fluxo in self.fluxo_repo.list_by_periodo(
                data_inicio=data_inicio,
                data_fim=data_fim,
                tipo=tipo,
                limit=limit,
                offset=offset,
            )
        ]

    def list_fluxo_por_conta_pagar(
        self,
        id_conta_pagar: int,
    ) -> list[FluxoCaixaReadSchema]:
        if self.conta_pagar_repo.get_by_id(id_conta_pagar) is None:
            raise FinanceiroError("Conta a pagar não encontrada.")

        return [
            self._to_fluxo_read(fluxo)
            for fluxo in self.fluxo_repo.list_by_conta_pagar(id_conta_pagar)
        ]

    def list_fluxo_por_conta_receber(
        self,
        id_conta_receber: int,
    ) -> list[FluxoCaixaReadSchema]:
        if self.conta_receber_repo.get_by_id(id_conta_receber) is None:
            raise FinanceiroError("Conta a receber não encontrada.")

        return [
            self._to_fluxo_read(fluxo)
            for fluxo in self.fluxo_repo.list_by_conta_receber(id_conta_receber)
        ]

    def resumo_fluxo_por_periodo(
        self,
        data_inicio: date,
        data_fim: date,
    ) -> dict[str, Decimal]:
        """Retorna totais agrupados por tipo (ex.: ENTRADA/SAIDA) no período."""
        if data_inicio > data_fim:
            raise FinanceiroError(
                "'data_inicio' não pode ser posterior a 'data_fim'."
            )

        return self.fluxo_repo.total_por_tipo(data_inicio, data_fim)

    # ============================================================
    # CONFIGURAÇÃO FINANCEIRA
    # ============================================================
    # Singleton (id_configuracao = 1). Não há create/delete — apenas
    # leitura e atualização do registro único.

    def get_configuracao_financeira(
        self,
    ) -> ConfiguracaoFinanceiraReadSchema | None:
        registro = self.configuracao_repo.get_configuracao()

        if registro is None:
            return None

        return ConfiguracaoFinanceiraReadSchema.model_validate(registro)

    def update_configuracao_financeira(
        self,
        payload: ConfiguracaoFinanceiraUpdateSchema,
    ) -> ConfiguracaoFinanceiraReadSchema:
        try:
            record = self.configuracao_repo.update(
                1, payload.model_dump(exclude_unset=True)
            )
        except IntegrityError as exc:
            raise FinanceiroError(
                "Não foi possível atualizar a configuração financeira."
            ) from exc

        if record is None:
            raise FinanceiroError(
                "Configuração financeira não encontrada. Verifique se o "
                "registro singleton (id=1) foi inicializado."
            )

        return ConfiguracaoFinanceiraReadSchema.model_validate(record)

    def get_limite_aprovacao_automatica(self) -> Decimal | None:
        """Atalho para consumidores externos (ex.: módulo de compras)
        que só precisam do limite, sem carregar a configuração inteira.
        """
        return self.configuracao_repo.get_limite_aprovacao_automatica()


    # ============================================================
    # LOOKUPS (combobox / selects do frontend)
    # ============================================================

    def list_compra_options(self) -> list[CompraOptionSchema]:
        return [
            CompraOptionSchema(id_compra=id_compra, label=label, valor_total=valor)
            for id_compra, label, valor in self.lookup_repo.list_compras_sem_conta_pagar()
        ]

    def list_manutencao_options(self) -> list[ManutencaoOptionSchema]:
        return [
            ManutencaoOptionSchema(
                id_manutencao=id_manutencao, label=label, tipo=tipo, custo=custo
            )
            for id_manutencao, label, tipo, custo in self.lookup_repo.list_manutencoes_sem_conta_pagar()
        ]

    def list_despesa_logistica_options(self) -> list[DespesaLogisticaOptionSchema]:
        return [
            DespesaLogisticaOptionSchema(id_despesa=id_despesa, label=label, valor=valor)
            for id_despesa, label, valor in self.lookup_repo.list_despesas_sem_conta_pagar()
        ]

    def list_venda_options(self) -> list[VendaOptionSchema]:
        return [
            VendaOptionSchema(
                id_venda=id_venda, label=label, valor_total=valor_total, data_venda=data_venda
            )
            for id_venda, label, valor_total, data_venda in self.lookup_repo.list_vendas_sem_conta_receber()
        ]

    def list_conta_pagar_options(self) -> list[ContaPagarOptionSchema]:
        return [
            ContaPagarOptionSchema(
                id_conta_pagar=id_conta,
                label=label,
                valor=valor,
                saldo=saldo,
                vencimento=vencimento,
                status=status,
            )
            for id_conta, label, valor, saldo, vencimento, status in self.lookup_repo.list_contas_pagar_abertas()
        ]

    def list_conta_receber_options(self) -> list[ContaReceberOptionSchema]:
        return [
            ContaReceberOptionSchema(
                id_conta_receber=id_conta,
                label=label,
                valor=valor,
                saldo=saldo,
                vencimento=vencimento,
                status=status,
            )
            for id_conta, label, valor, saldo, vencimento, status in self.lookup_repo.list_contas_receber_abertas()
        ]

    def list_forma_pagamento_options(self) -> list[FormaPagamentoOptionSchema]:
        return [
            FormaPagamentoOptionSchema(valor=forma)
            for forma in self.lookup_repo.list_formas_pagamento_utilizadas()
        ]
