"""Acesso a dados do domínio financeiro."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.base_repository import BaseRepository
from app.core.database import get_session

from app.compras.models.purchase import PurchaseModel

from app.financeiro.enum import StatusContaPagarEnum, StatusContaReceberEnum
from app.financeiro.models import (
    ContaPagarModel,
    PagamentoModel,
    ContaReceberModel,
    RecebimentoModel,
    FluxoCaixaModel,
    ConfiguracaoFinanceiraModel,
)
from app.financeiro.refs import (
    VendaRef,
    ManutencaoRef,
    DespesaOperacaoLogisticaRef,
)

_STATUS_CONTA_PAGAR_ABERTOS = (
    StatusContaPagarEnum.ABERTA,
    StatusContaPagarEnum.PARCIALMENTE_PAGA,
)

_STATUS_CONTA_RECEBER_ABERTOS = (
    StatusContaReceberEnum.ABERTA,
    StatusContaReceberEnum.PARCIALMENTE_RECEBIDA,
)


class ContaPagarRepository(BaseRepository[ContaPagarModel]):
    model = ContaPagarModel

    def list_com_detalhes(
        self,
        status: StatusContaPagarEnum | None = None,
        vencendo_em: int | None = None,
        vencidas: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[
        tuple[
            ContaPagarModel,
            str | None,
            Decimal | None,
            str | None,
            Decimal | None,
            date | None,
            str | None,
            str | None,
            date | None,
            Decimal,
            Decimal,
        ]
    ]:
        """Lista contas a pagar com informações da origem, pagamentos e saldo.

        Filtros opcionais:
        - status: filtra pelo status da conta.
        - vencendo_em: lista contas abertas com vencimento nos próximos N dias.
        - vencidas: lista contas abertas cujo vencimento já passou.

        Retorna:
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
        )
        """

        with get_session() as session:
            totais = (
                select(
                    PagamentoModel.id_conta_pagar,
                    func.sum(PagamentoModel.valor_pago).label("valor_pago"),
                )
                .group_by(PagamentoModel.id_conta_pagar)
                .subquery()
            )

            query = (
                select(
                    ContaPagarModel,
                    PurchaseModel.valor_total,
                    ManutencaoRef.tipo,
                    ManutencaoRef.custo,
                    ManutencaoRef.dt_inicio,
                    DespesaOperacaoLogisticaRef.descricao,
                    DespesaOperacaoLogisticaRef.tipo,
                    DespesaOperacaoLogisticaRef.data_despesa,
                    func.coalesce(
                        totais.c.valor_pago,
                        Decimal("0"),
                    ).label("valor_pago"),
                    (
                        ContaPagarModel.valor
                        - func.coalesce(
                            totais.c.valor_pago,
                            Decimal("0"),
                        )
                    ).label("saldo"),
                )
                .outerjoin(
                    PurchaseModel,
                    PurchaseModel.id_compra == ContaPagarModel.id_compra,
                )
                .outerjoin(
                    ManutencaoRef,
                    ManutencaoRef.id_manutencao == ContaPagarModel.id_manutencao,
                )
                .outerjoin(
                    DespesaOperacaoLogisticaRef,
                    DespesaOperacaoLogisticaRef.id_despesa
                    == ContaPagarModel.id_despesa_logistica,
                )
                .outerjoin(
                    totais,
                    totais.c.id_conta_pagar
                    == ContaPagarModel.id_conta_pagar,
                )
            )

            if status is not None:
                query = query.where(
                    ContaPagarModel.status == status
                )

            hoje = date.today()

            if vencendo_em is not None:
                limite = hoje + timedelta(days=vencendo_em)

                query = query.where(
                    ContaPagarModel.vencimento.isnot(None),
                    ContaPagarModel.vencimento >= hoje,
                    ContaPagarModel.vencimento <= limite,
                    ContaPagarModel.status.in_(
                        _STATUS_CONTA_PAGAR_ABERTOS
                    ),
                )

            if vencidas:
                query = query.where(
                    ContaPagarModel.vencimento.isnot(None),
                    ContaPagarModel.vencimento < hoje,
                    ContaPagarModel.status.in_(
                        _STATUS_CONTA_PAGAR_ABERTOS
                    ),
                )

            rows = session.execute(
                query
                .order_by(
                    ContaPagarModel.id_conta_pagar
                )
                .limit(limit)
                .offset(offset)
            ).all()

            result = []

            for (
                conta,
                compra_valor,
                manutencao_tipo,
                manutencao_custo,
                manutencao_data,
                despesa_descricao,
                despesa_tipo,
                despesa_data,
                valor_pago,
                saldo,
            ) in rows:
                session.expunge(conta)

                result.append(
                    (
                        conta,
                        self._origem(conta),
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
                )

            return result

    def get_com_detalhes(
        self, id_conta_pagar: int
    ) -> tuple[
        ContaPagarModel,
        str | None,
        Decimal | None,
        str | None,
        Decimal | None,
        date | None,
        str | None,
        str | None,
        date | None,
        Decimal,
        Decimal,
    ] | None:
        """Busca uma conta a pagar específica com informações da origem e valores pagos."""
        with get_session() as session:
            totais = (
                select(
                    PagamentoModel.id_conta_pagar,
                    func.sum(PagamentoModel.valor_pago).label("valor_pago"),
                )
                .group_by(PagamentoModel.id_conta_pagar)
                .subquery()
            )

            row = session.execute(
                select(
                    ContaPagarModel,
                    PurchaseModel.valor_total,
                    ManutencaoRef.tipo,
                    ManutencaoRef.custo,
                    ManutencaoRef.dt_inicio,
                    DespesaOperacaoLogisticaRef.descricao,
                    DespesaOperacaoLogisticaRef.tipo,
                    DespesaOperacaoLogisticaRef.data_despesa,
                    func.coalesce(totais.c.valor_pago, Decimal("0")).label("valor_pago"),
                    (
                        ContaPagarModel.valor
                        - func.coalesce(totais.c.valor_pago, Decimal("0"))
                    ).label("saldo"),
                )
                .outerjoin(
                    PurchaseModel,
                    PurchaseModel.id_compra == ContaPagarModel.id_compra,
                )
                .outerjoin(
                    ManutencaoRef,
                    ManutencaoRef.id_manutencao == ContaPagarModel.id_manutencao,
                )
                .outerjoin(
                    DespesaOperacaoLogisticaRef,
                    DespesaOperacaoLogisticaRef.id_despesa
                    == ContaPagarModel.id_despesa_logistica,
                )
                .outerjoin(
                    totais,
                    totais.c.id_conta_pagar == ContaPagarModel.id_conta_pagar,
                )
                .where(ContaPagarModel.id_conta_pagar == id_conta_pagar)
            ).first()

            if row is None:
                return None

            (
                conta,
                compra_valor,
                manutencao_tipo,
                manutencao_custo,
                manutencao_data,
                despesa_descricao,
                despesa_tipo,
                despesa_data,
                valor_pago,
                saldo,
            ) = row

            session.expunge(conta)

            return (
                conta,
                self._origem(conta),
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

    def get_by_compra(self, id_compra: int) -> ContaPagarModel | None:
        """Busca a conta a pagar vinculada a uma compra, se existir."""
        with get_session() as session:
            registro = session.scalar(
                select(ContaPagarModel).where(ContaPagarModel.id_compra == id_compra)
            )
            if registro is not None:
                session.expunge(registro)
            return registro

    def get_by_manutencao(self, id_manutencao: int) -> ContaPagarModel | None:
        """Busca a conta a pagar vinculada a uma manutenção, se existir."""
        with get_session() as session:
            registro = session.scalar(
                select(ContaPagarModel).where(
                    ContaPagarModel.id_manutencao == id_manutencao
                )
            )
            if registro is not None:
                session.expunge(registro)
            return registro

    def get_by_despesa_logistica(self, id_despesa: int) -> ContaPagarModel | None:
        """Busca a conta a pagar vinculada a uma despesa logística, se existir."""
        with get_session() as session:
            registro = session.scalar(
                select(ContaPagarModel).where(
                    ContaPagarModel.id_despesa_logistica == id_despesa
                )
            )
            if registro is not None:
                session.expunge(registro)
            return registro

    def exists_by_compra(self, id_compra: int) -> bool:
        """Verifica se já existe conta a pagar vinculada a uma compra."""
        with get_session() as session:
            return (
                session.scalar(
                    select(ContaPagarModel.id_conta_pagar)
                    .where(ContaPagarModel.id_compra == id_compra)
                    .limit(1)
                )
                is not None
            )

    def exists_by_manutencao(self, id_manutencao: int) -> bool:
        """Verifica se já existe conta a pagar vinculada a uma manutenção."""
        with get_session() as session:
            return (
                session.scalar(
                    select(ContaPagarModel.id_conta_pagar)
                    .where(ContaPagarModel.id_manutencao == id_manutencao)
                    .limit(1)
                )
                is not None
            )

    def exists_by_despesa_logistica(self, id_despesa: int) -> bool:
        """Verifica se já existe conta a pagar vinculada a uma despesa logística."""
        with get_session() as session:
            return (
                session.scalar(
                    select(ContaPagarModel.id_conta_pagar)
                    .where(ContaPagarModel.id_despesa_logistica == id_despesa)
                    .limit(1)
                )
                is not None
            )

    @staticmethod
    def _origem(conta: ContaPagarModel) -> str | None:
        if conta.id_compra is not None:
            return "compra"
        if conta.id_manutencao is not None:
            return "manutencao"
        if conta.id_despesa_logistica is not None:
            return "despesa_logistica"
        return None


class PagamentoRepository(BaseRepository[PagamentoModel]):
    model = PagamentoModel

    def list_by_conta_pagar(self, id_conta_pagar: int) -> list[PagamentoModel]:
        """Lista os pagamentos já registrados para uma conta a pagar."""
        with get_session() as session:
            registros = session.scalars(
                select(PagamentoModel)
                .where(PagamentoModel.id_conta_pagar == id_conta_pagar)
                .order_by(PagamentoModel.data_pagamento.desc())
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_com_detalhes(
        self, limit: int = 50, offset: int = 0
    ) -> list[tuple[PagamentoModel, date | None, StatusContaPagarEnum | None, Decimal]]:
        """Lista pagamentos já trazendo vencimento, status e saldo da conta a pagar associada."""
        with get_session() as session:
            totais = (
                select(
                    PagamentoModel.id_conta_pagar,
                    func.sum(PagamentoModel.valor_pago).label("total_pago"),
                )
                .group_by(PagamentoModel.id_conta_pagar)
                .subquery()
            )

            rows = session.execute(
                select(
                    PagamentoModel,
                    ContaPagarModel.vencimento,
                    ContaPagarModel.status,
                    (
                        ContaPagarModel.valor
                        - func.coalesce(totais.c.total_pago, Decimal("0"))
                    ).label("saldo"),
                )
                .outerjoin(
                    ContaPagarModel,
                    ContaPagarModel.id_conta_pagar == PagamentoModel.id_conta_pagar,
                )
                .outerjoin(
                    totais,
                    totais.c.id_conta_pagar == ContaPagarModel.id_conta_pagar,
                )
                .order_by(PagamentoModel.data_pagamento.desc())
                .limit(limit)
                .offset(offset)
            ).all()

            result = []
            for pagamento, vencimento, status, saldo in rows:
                session.expunge(pagamento)
                result.append((pagamento, vencimento, status, saldo))

            return result
    
    def total_pago_por_conta(self, id_conta_pagar: int) -> Decimal:
        """Soma tudo que já foi pago para uma conta a pagar (para calcular o saldo)."""
        with get_session() as session:
            total = session.scalar(
                select(func.coalesce(func.sum(PagamentoModel.valor_pago), Decimal("0"))).where(
                    PagamentoModel.id_conta_pagar == id_conta_pagar
                )
            )
            return total or Decimal("0")

    def exists_by_conta_pagar(self, id_conta_pagar: int) -> bool:
        """Verifica se a conta a pagar possui pagamentos registrados."""
        with get_session() as session:
            return (
                session.scalar(
                    select(PagamentoModel.id_pagamento)
                    .where(PagamentoModel.id_conta_pagar == id_conta_pagar)
                    .limit(1)
                )
                is not None
            )


class ContaReceberRepository(BaseRepository[ContaReceberModel]):
    model = ContaReceberModel

    def list_com_detalhes(
        self,
        status: StatusContaReceberEnum | None = None,
        vencendo_em: int | None = None,
        vencidas: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[
        tuple[
            ContaReceberModel,
            Decimal | None,
            date | None,
            Decimal,
            Decimal,
        ]
    ]:
        """Lista contas a receber com dados da venda, recebimentos e saldo.

        Filtros opcionais:
        - status: filtra pelo status da conta.
        - vencendo_em: lista contas abertas com vencimento nos próximos N dias.
        - vencidas: lista contas abertas cujo vencimento já passou.

        Retorna:
        (
            conta,
            valor_venda,
            data_venda,
            valor_recebido,
            saldo,
        )
        """

        with get_session() as session:
            totais = (
                select(
                    RecebimentoModel.id_conta_receber,
                    func.sum(
                        RecebimentoModel.valor_recebido
                    ).label("valor_recebido"),
                )
                .group_by(RecebimentoModel.id_conta_receber)
                .subquery()
            )

            query = (
                select(
                    ContaReceberModel,
                    VendaRef.valor_total,
                    VendaRef.data_venda,
                    func.coalesce(
                        totais.c.valor_recebido,
                        Decimal("0"),
                    ).label("valor_recebido"),
                    (
                        ContaReceberModel.valor
                        - func.coalesce(
                            totais.c.valor_recebido,
                            Decimal("0"),
                        )
                    ).label("saldo"),
                )
                .select_from(ContaReceberModel)
                .outerjoin(
                    VendaRef,
                    VendaRef.id_venda
                    == ContaReceberModel.id_venda,
                )
                .outerjoin(
                    totais,
                    totais.c.id_conta_receber
                    == ContaReceberModel.id_conta_receber,
                )
            )

            if status is not None:
                query = query.where(
                    ContaReceberModel.status == status
                )

            hoje = date.today()

            if vencendo_em is not None:
                limite = hoje + timedelta(days=vencendo_em)

                query = query.where(
                    ContaReceberModel.vencimento.isnot(None),
                    ContaReceberModel.vencimento >= hoje,
                    ContaReceberModel.vencimento <= limite,
                    ContaReceberModel.status.in_(
                        _STATUS_CONTA_RECEBER_ABERTOS
                    ),
                )

            if vencidas:
                query = query.where(
                    ContaReceberModel.vencimento.isnot(None),
                    ContaReceberModel.vencimento < hoje,
                    ContaReceberModel.status.in_(
                        _STATUS_CONTA_RECEBER_ABERTOS
                    ),
                )

            rows = session.execute(
                query
                .order_by(
                    ContaReceberModel.id_conta_receber
                )
                .limit(limit)
                .offset(offset)
            ).all()

            result = []

            for (
                conta,
                valor_venda,
                data_venda,
                valor_recebido,
                saldo,
            ) in rows:
                session.expunge(conta)

                result.append(
                    (
                        conta,
                        valor_venda,
                        data_venda,
                        valor_recebido,
                        saldo,
                    )
                )

            return result

    def get_com_detalhes(
        self, id_conta_receber: int
    ) -> tuple[
        ContaReceberModel,
        Decimal | None,
        date | None,
        Decimal,
        Decimal,
    ] | None:
        """Busca uma conta a receber com dados da venda, valor recebido e saldo."""
        with get_session() as session:
            totais = (
                select(
                    RecebimentoModel.id_conta_receber,
                    func.sum(RecebimentoModel.valor_recebido).label("valor_recebido"),
                )
                .group_by(RecebimentoModel.id_conta_receber)
                .subquery()
            )

            row = session.execute(
                select(
                    ContaReceberModel,
                    VendaRef.valor_total,
                    VendaRef.data_venda,
                    func.coalesce(totais.c.valor_recebido, Decimal("0")).label("valor_recebido"),
                    (
                        ContaReceberModel.valor
                        - func.coalesce(totais.c.valor_recebido, Decimal("0"))
                    ).label("saldo"),
                )
                .select_from(ContaReceberModel)
                .outerjoin(
                    VendaRef,
                    VendaRef.id_venda == ContaReceberModel.id_venda,
                )
                .outerjoin(
                    totais,
                    totais.c.id_conta_receber == ContaReceberModel.id_conta_receber,
                )
                .where(ContaReceberModel.id_conta_receber == id_conta_receber)
            ).first()

            if row is None:
                return None

            conta, valor_venda, data_venda, valor_recebido, saldo = row

            session.expunge(conta)

            return (
                conta,
                valor_venda,
                data_venda,
                valor_recebido,
                saldo,
            )

    def get_by_venda(self, id_venda: int) -> ContaReceberModel | None:
        """Busca a conta a receber vinculada a uma venda, se existir."""
        with get_session() as session:
            registro = session.scalar(
                select(ContaReceberModel).where(ContaReceberModel.id_venda == id_venda)
            )
            if registro is not None:
                session.expunge(registro)
            return registro

    def exists_by_venda(self, id_venda: int) -> bool:
        """Verifica se já existe conta a receber vinculada a uma venda."""
        with get_session() as session:
            return (
                session.scalar(
                    select(ContaReceberModel.id_conta_receber)
                    .where(ContaReceberModel.id_venda == id_venda)
                    .limit(1)
                )
                is not None
            )


class RecebimentoRepository(BaseRepository[RecebimentoModel]):
    model = RecebimentoModel

    def list_by_conta_receber(self, id_conta_receber: int) -> list[RecebimentoModel]:
        """Lista os recebimentos já registrados para uma conta a receber."""
        with get_session() as session:
            registros = session.scalars(
                select(RecebimentoModel)
                .where(RecebimentoModel.id_conta_receber == id_conta_receber)
                .order_by(RecebimentoModel.data_recebimento.desc())
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_com_detalhes(
        self, limit: int = 50, offset: int = 0
    ) -> list[tuple[RecebimentoModel, date | None, StatusContaReceberEnum | None, Decimal]]:
        """Lista recebimentos já trazendo vencimento, status e saldo da conta a receber associada."""
        with get_session() as session:
            totais = (
                select(
                    RecebimentoModel.id_conta_receber,
                    func.sum(RecebimentoModel.valor_recebido).label("total_recebido"),
                )
                .group_by(RecebimentoModel.id_conta_receber)
                .subquery()
            )

            rows = session.execute(
                select(
                    RecebimentoModel,
                    ContaReceberModel.vencimento,
                    ContaReceberModel.status,
                    (
                        ContaReceberModel.valor
                        - func.coalesce(totais.c.total_recebido, Decimal("0"))
                    ).label("saldo"),
                )
                .outerjoin(
                    ContaReceberModel,
                    ContaReceberModel.id_conta_receber
                    == RecebimentoModel.id_conta_receber,
                )
                .outerjoin(
                    totais,
                    totais.c.id_conta_receber
                    == ContaReceberModel.id_conta_receber,
                )
                .order_by(RecebimentoModel.data_recebimento.desc())
                .limit(limit)
                .offset(offset)
            ).all()

            result = []
            for recebimento, vencimento, status, saldo in rows:
                session.expunge(recebimento)
                result.append((recebimento, vencimento, status, saldo))

            return result
    
    def total_recebido_por_conta(self, id_conta_receber: int) -> Decimal:
        """Soma tudo que já foi recebido para uma conta a receber (para calcular o saldo)."""
        with get_session() as session:
            total = session.scalar(
                select(func.coalesce(func.sum(RecebimentoModel.valor_recebido), Decimal("0"))).where(
                    RecebimentoModel.id_conta_receber == id_conta_receber
                )
            )
            return total or Decimal("0")

    def exists_by_conta_receber(self, id_conta_receber: int) -> bool:
        """Verifica se a conta a receber possui recebimentos registrados."""
        with get_session() as session:
            return (
                session.scalar(
                    select(RecebimentoModel.id_recebimento)
                    .where(RecebimentoModel.id_conta_receber == id_conta_receber)
                    .limit(1)
                )
                is not None
            )


class FluxoCaixaRepository(BaseRepository[FluxoCaixaModel]):
    """Somente leitura pela API — os lançamentos são criados pelo service

    a partir de pagamentos/recebimentos confirmados, nunca diretamente.
    """

    model = FluxoCaixaModel

    def list_by_periodo(
        self,
        data_inicio: date,
        data_fim: date,
        tipo: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FluxoCaixaModel]:
        """Lista movimentações de caixa num intervalo de datas (paginado)."""
        with get_session() as session:
            query = (
                select(FluxoCaixaModel)
                .where(
                    FluxoCaixaModel.data_movimento.isnot(None),
                    FluxoCaixaModel.data_movimento.between(
                        data_inicio,
                        data_fim,
                    ),
                )
            )

            if tipo is not None:
                query = query.where(FluxoCaixaModel.tipo == tipo)

            registros = session.scalars(
                query.order_by(
                    FluxoCaixaModel.data_movimento.desc()
                )
                .limit(limit)
                .offset(offset)
            ).all()

            for registro in registros:
                session.expunge(registro)

            return list(registros)

    def list_by_conta_pagar(self, id_conta_pagar: int) -> list[FluxoCaixaModel]:
        """Lista lançamentos de caixa originados de uma conta a pagar específica."""
        with get_session() as session:
            registros = session.scalars(
                select(FluxoCaixaModel).where(
                    FluxoCaixaModel.id_conta_pagar == id_conta_pagar
                )
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def list_by_conta_receber(self, id_conta_receber: int) -> list[FluxoCaixaModel]:
        """Lista lançamentos de caixa originados de uma conta a receber específica."""
        with get_session() as session:
            registros = session.scalars(
                select(FluxoCaixaModel).where(
                    FluxoCaixaModel.id_conta_receber == id_conta_receber
                )
            ).all()
            for registro in registros:
                session.expunge(registro)
            return list(registros)

    def get_by_pagamento(self, id_pagamento: int) -> FluxoCaixaModel | None:
        """Busca o lançamento de caixa gerado por um pagamento específico."""
        with get_session() as session:
            registro = session.scalar(
                select(FluxoCaixaModel).where(
                    FluxoCaixaModel.id_pagamento == id_pagamento
                )
            )
            if registro is not None:
                session.expunge(registro)
            return registro

    def get_by_recebimento(self, id_recebimento: int) -> FluxoCaixaModel | None:
        """Busca o lançamento de caixa gerado por um recebimento específico."""
        with get_session() as session:
            registro = session.scalar(
                select(FluxoCaixaModel).where(
                    FluxoCaixaModel.id_recebimento == id_recebimento
                )
            )
            if registro is not None:
                session.expunge(registro)
            return registro

    def total_por_tipo(
        self, data_inicio: date, data_fim: date
    ) -> dict[str, Decimal]:
        """Agrupa o total movimentado por tipo (ex.: ENTRADA/SAIDA) num período."""
        with get_session() as session:
            rows = session.execute(
                select(
                    FluxoCaixaModel.tipo,
                    func.coalesce(func.sum(FluxoCaixaModel.valor), Decimal("0")),
                )
                .where(
                    FluxoCaixaModel.data_movimento.isnot(None),
                    FluxoCaixaModel.data_movimento.between(data_inicio, data_fim),
                )
                .group_by(FluxoCaixaModel.tipo)
            ).all()
            return {tipo or "INDEFINIDO": total for tipo, total in rows}


class ConfiguracaoFinanceiraRepository(BaseRepository[ConfiguracaoFinanceiraModel]):
    """A tabela é um singleton (chk_configuracao_financeira_unica garante id=1)."""

    model = ConfiguracaoFinanceiraModel

    def get_configuracao(self) -> ConfiguracaoFinanceiraModel | None:
        """Retorna a configuração financeira global (linha única, id=1)."""
        with get_session() as session:
            registro = session.get(ConfiguracaoFinanceiraModel, 1)
            if registro is not None:
                session.expunge(registro)
            return registro

    def get_limite_aprovacao_automatica(self) -> Decimal | None:
        """Atalho para obter apenas o limite de aprovação automática configurado."""
        with get_session() as session:
            return session.scalar(
                select(ConfiguracaoFinanceiraModel.limite_aprovacao_automatica).where(
                    ConfiguracaoFinanceiraModel.id_configuracao == 1
                )
            )


class FinanceiroLookupRepository:
    """Consultas utilizadas para preencher comboboxes e selects no frontend."""

    def list_manutencoes_sem_conta_pagar(self) -> list[tuple[int, str, str | None, Decimal | None]]:
        """Manutenções que ainda não possuem conta a pagar vinculada."""
        with get_session() as session:
            rows = session.execute(
                select(
                    ManutencaoRef.id_manutencao,
                    ManutencaoRef.tipo,
                    ManutencaoRef.custo,
                )
                .outerjoin(
                    ContaPagarModel,
                    ContaPagarModel.id_manutencao == ManutencaoRef.id_manutencao,
                )
                .where(ContaPagarModel.id_conta_pagar.is_(None))
            ).all()
            return [
                (
                    id_manutencao,
                    f"Manutenção #{id_manutencao} ({tipo or 'sem tipo'})",
                    tipo,
                    custo,
                )
                for id_manutencao, tipo, custo in rows
            ]

    def list_despesas_sem_conta_pagar(self) -> list[tuple[int, str, Decimal]]:
        """Despesas de operação logística que ainda não possuem conta a pagar vinculada."""
        with get_session() as session:
            rows = session.execute(
                select(
                    DespesaOperacaoLogisticaRef.id_despesa,
                    DespesaOperacaoLogisticaRef.descricao,
                    DespesaOperacaoLogisticaRef.valor,
                )
                .outerjoin(
                    ContaPagarModel,
                    ContaPagarModel.id_despesa_logistica
                    == DespesaOperacaoLogisticaRef.id_despesa,
                )
                .where(ContaPagarModel.id_conta_pagar.is_(None))
            ).all()
            return [
                (id_despesa, f"{descricao} — R$ {valor}", valor)
                for id_despesa, descricao, valor in rows
            ]

    def list_vendas_sem_conta_receber(self) -> list[tuple[int, str, Decimal, date | None]]:
        """Vendas que ainda não possuem conta a receber vinculada."""
        with get_session() as session:
            rows = session.execute(
                select(VendaRef.id_venda, VendaRef.valor_total, VendaRef.data_venda)
                .select_from(VendaRef)
                .outerjoin(
                    ContaReceberModel, ContaReceberModel.id_venda == VendaRef.id_venda
                )
                .where(ContaReceberModel.id_conta_receber.is_(None))
            ).all()
            return [
                (id_venda, f"Venda #{id_venda} — R$ {valor_total}", valor_total, data_venda)
                for id_venda, valor_total, data_venda in rows
            ]

    def list_contas_pagar_abertas(self) -> list[tuple[int, str, Decimal, Decimal, date | None, StatusContaPagarEnum]]:
        """Contas a pagar em aberto/parcialmente pagas, candidatas a receber um pagamento."""
        with get_session() as session:
            rows = session.execute(
                select(
                    ContaPagarModel.id_conta_pagar,
                    ContaPagarModel.valor,
                    ContaPagarModel.vencimento,
                    ContaPagarModel.status,
                    (
                        ContaPagarModel.valor
                        - func.coalesce(func.sum(PagamentoModel.valor_pago), Decimal("0"))
                    ).label("saldo"),
                )
                .outerjoin(
                    PagamentoModel,
                    PagamentoModel.id_conta_pagar
                    == ContaPagarModel.id_conta_pagar,
                )
                .where(
                    ContaPagarModel.status.in_(_STATUS_CONTA_PAGAR_ABERTOS)
                )
                .group_by(
                    ContaPagarModel.id_conta_pagar,
                    ContaPagarModel.valor,
                    ContaPagarModel.vencimento,
                    ContaPagarModel.status,
                )
            ).all()
            return [
                (
                    id_conta,
                    f"Conta #{id_conta} — R$ {saldo}",
                    valor,
                    saldo,
                    vencimento,
                    status,
                )
                for (
                    id_conta,
                    valor,
                    vencimento,
                    status,
                    saldo,
                ) in rows
            ]

    def list_contas_receber_abertas(self) -> list[tuple[int, str, Decimal, Decimal, date | None, StatusContaReceberEnum]]:
        """Contas a receber em aberto/parcialmente recebidas, candidatas a um recebimento."""
        with get_session() as session:
            rows = session.execute(
                select(
                    ContaReceberModel.id_conta_receber,
                    ContaReceberModel.valor,
                    ContaReceberModel.vencimento,
                    ContaReceberModel.status,
                    (
                        ContaReceberModel.valor
                        - func.coalesce(func.sum(RecebimentoModel.valor_recebido), Decimal("0"))
                    ).label("saldo"),
                )
                .outerjoin(
                    RecebimentoModel,
                    RecebimentoModel.id_conta_receber
                    == ContaReceberModel.id_conta_receber,
                )
                .where(ContaReceberModel.status.in_(_STATUS_CONTA_RECEBER_ABERTOS))
                .group_by(
                    ContaReceberModel.id_conta_receber,
                    ContaReceberModel.valor,
                    ContaReceberModel.vencimento,
                    ContaReceberModel.status,
                )
            ).all()
            return [
                (
                    id_conta,
                    f"Conta #{id_conta} — R$ {saldo}",
                    valor,
                    saldo,
                    vencimento,
                    status,
                )
                for (
                    id_conta,
                    valor,
                    vencimento,
                    status,
                    saldo,
                ) in rows
            ]

    def list_formas_pagamento_utilizadas(self) -> list[str]:
        """Formas de pagamento distintas já utilizadas em pagamentos ou recebimentos."""
        with get_session() as session:
            formas_pagamento = set(
                session.scalars(
                    select(PagamentoModel.forma_pagamento).where(
                        PagamentoModel.forma_pagamento.isnot(None)
                    )
                ).all()
            )
            formas_recebimento = set(
                session.scalars(
                    select(RecebimentoModel.forma_pagamento).where(
                        RecebimentoModel.forma_pagamento.isnot(None)
                    )
                ).all()
            )
            return sorted(
                forma
                for forma in (formas_pagamento | formas_recebimento)
                if forma
            )
        
    def list_compras_sem_conta_pagar(
        self,
    ) -> list[tuple[int, str, Decimal]]:
        """Compras que ainda não possuem conta a pagar vinculada."""
        with get_session() as session:
            rows = session.execute(
                select(
                    PurchaseModel.id_compra,
                    PurchaseModel.valor_total,
                )
                .outerjoin(
                    ContaPagarModel,
                    ContaPagarModel.id_compra == PurchaseModel.id_compra,
                )
                .where(ContaPagarModel.id_conta_pagar.is_(None))
            ).all()

            return [
                (
                    id_compra,
                    f"Compra #{id_compra} — R$ {valor_total}",
                    valor_total,
                )
                for id_compra, valor_total in rows
            ]
