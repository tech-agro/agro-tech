"""Modelos ORM do domínio financeiro."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.financeiro.enum import StatusContaPagarEnum, StatusContaReceberEnum


class ContaPagarModel(Base):
    """Representa uma conta a pagar do sistema.

    Uma conta a pagar pode ser originada por uma compra,
    uma manutenção ou uma despesa de operação logística.
    Corresponde à tabela `conta_pagar`.
    """

    __tablename__ = "conta_pagar"

    __table_args__ = (
        CheckConstraint("valor >= 0", name="chk_conta_pagar_valor_pos"),
        CheckConstraint(
            """
            (
                (CASE WHEN id_compra IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN id_manutencao IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN id_despesa_logistica IS NOT NULL THEN 1 ELSE 0 END)
            ) = 1
            """,
            name="chk_conta_pagar_origem",
        ),
    )

    id_conta_pagar: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_compra: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("compra.id_compra"),
    )

    id_manutencao: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("manutencao.id_manutencao"),
    )

    id_despesa_logistica: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("despesa_operacao_logistica.id_despesa"),
    )

    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    vencimento: Mapped[date | None] = mapped_column(Date)

    status: Mapped[StatusContaPagarEnum] = mapped_column(
        Enum(
            StatusContaPagarEnum,
            name="status_conta_pagar_enum",
            create_type=False,
        ),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ContaPagarModel "
            f"id={self.id_conta_pagar} "
            f"valor={self.valor}>"
        )


class PagamentoModel(Base):
    """Representa um pagamento realizado para uma conta a pagar.

    Corresponde à tabela `pagamento`.
    """

    __tablename__ = "pagamento"

    __table_args__ = (
        CheckConstraint(
            "valor_pago >= 0",
            name="chk_pagamento_valor_pos",
        ),
    )

    id_pagamento: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_conta_pagar: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conta_pagar.id_conta_pagar"),
        nullable=False,
    )

    valor_pago: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    data_pagamento: Mapped[date | None] = mapped_column(Date)

    forma_pagamento: Mapped[str | None] = mapped_column(String(80),)

    def __repr__(self) -> str:
        return (
            f"<PagamentoModel "
            f"id={self.id_pagamento} "
            f"id_conta_pagar={self.id_conta_pagar}>"
        )


class ContaReceberModel(Base):
    """Representa uma conta a receber originada de uma venda.

    Corresponde à tabela `conta_receber`.
    """

    __tablename__ = "conta_receber"

    __table_args__ = (
        CheckConstraint(
            "valor >= 0",
            name="chk_conta_receber_valor_pos",
        ),
    )

    id_conta_receber: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_venda: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("venda.id_venda"),
        nullable=False,
    )

    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    vencimento: Mapped[date | None] = mapped_column(Date)

    status: Mapped[StatusContaReceberEnum] = mapped_column(
        Enum(
            StatusContaReceberEnum,
            name="status_conta_receber_enum",
            create_type=False,
        ),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return (
            f"<ContaReceberModel "
            f"id={self.id_conta_receber} "
            f"valor={self.valor}>"
        )


class RecebimentoModel(Base):
    """Representa um recebimento referente a uma conta a receber.

    Corresponde à tabela `recebimento`.
    """

    __tablename__ = "recebimento"

    __table_args__ = (
        CheckConstraint(
            "valor_recebido >= 0",
            name="chk_recebimento_valor_pos",
        ),
    )

    id_recebimento: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_conta_receber: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conta_receber.id_conta_receber"),
        nullable=False,
    )

    valor_recebido: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    data_recebimento: Mapped[date | None] = mapped_column(Date)

    forma_pagamento: Mapped[str | None] = mapped_column(String(80))

    def __repr__(self) -> str:
        return (
            f"<RecebimentoModel "
            f"id={self.id_recebimento} "
            f"id_conta_receber={self.id_conta_receber}>"
        )


class FluxoCaixaModel(Base):
    """Representa uma movimentação do fluxo de caixa.

    Cada movimentação deve estar vinculada a exatamente uma
    conta a pagar ou uma conta a receber.

    Corresponde à tabela `fluxo_caixa`.
    """

    __tablename__ = "fluxo_caixa"

    __table_args__ = (
        CheckConstraint(
            "valor >= 0",
            name="chk_fluxo_caixa_valor_pos",
        ),
        CheckConstraint(
            """
            (
                (CASE WHEN id_conta_pagar IS NOT NULL THEN 1 ELSE 0 END) +
                (CASE WHEN id_conta_receber IS NOT NULL THEN 1 ELSE 0 END)
            ) = 1
            """,
            name="chk_fluxo_caixa_origem",
        ),
    )

    id_fluxo: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_conta_pagar: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("conta_pagar.id_conta_pagar"))

    id_conta_receber: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("conta_receber.id_conta_receber"))

    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    tipo: Mapped[str | None] = mapped_column(String(50))

    data_movimento: Mapped[date | None] = mapped_column(Date)

    def __repr__(self) -> str:
        return (
            f"<FluxoCaixaModel "
            f"id={self.id_fluxo} "
            f"valor={self.valor}>"
        )


class ConfiguracaoFinanceiraModel(Base):
    """Representa a configuração global do módulo financeiro.

    Atualmente armazena apenas o limite para aprovação automática
    de compras.

    Corresponde à tabela `configuracao_financeira`.
    """

    __tablename__ = "configuracao_financeira"

    __table_args__ = (
        CheckConstraint(
            "id_configuracao = 1",
            name="chk_configuracao_financeira_unica",
        ),
        CheckConstraint(
            "limite_aprovacao_automatica >= 0",
            name="chk_limite_aprovacao_pos",
        ),
    )

    id_configuracao: Mapped[int] = mapped_column(
        SmallInteger,
        primary_key=True,
        default=1,
    )

    limite_aprovacao_automatica: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ConfiguracaoFinanceiraModel "
            f"limite={self.limite_aprovacao_automatica}>"
        )