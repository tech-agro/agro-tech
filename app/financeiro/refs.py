"""Minimal ORM stubs para resolver FKs do módulo financeiro.

As tabelas pertencem a outros módulos. O Financeiro mantém apenas
os campos necessários para consultas e exibição de informações.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class VendaRef(Base):
    """Representa minimamente uma venda."""

    __tablename__ = "venda"
    __table_args__ = {"extend_existing": True}

    id_venda: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    data_venda: Mapped[date | None] = mapped_column(Date)


class ManutencaoRef(Base):
    """Representa minimamente uma manutenção."""

    __tablename__ = "manutencao"
    __table_args__ = {"extend_existing": True}

    id_manutencao: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tipo: Mapped[str | None] = mapped_column(String(50))
    custo: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    dt_inicio: Mapped[date | None] = mapped_column(Date)


class DespesaOperacaoLogisticaRef(Base):
    """Representa minimamente uma despesa de operação logística."""

    __tablename__ = "despesa_operacao_logistica"
    __table_args__ = {"extend_existing": True}

    id_despesa: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_operacao: Mapped[int] = mapped_column(BigInteger, nullable=False)
    descricao: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(50))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    data_despesa: Mapped[date] = mapped_column(Date, nullable=False)


class AplicacaoDefensivoRef(Base):
    """Representa minimamente uma aplicação de defensivo."""

    __tablename__ = "aplicacao_defensivo"
    __table_args__ = {"extend_existing": True}

    id_aplicacao: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_insumo: Mapped[int] = mapped_column(BigInteger, nullable=False)
    volume_aplicado: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    dt_aplicacao: Mapped[date | None] = mapped_column(Date)


class ProdutoPrecoRef(Base):
    """Produto mínimo para preço/nome em lookups financeiros."""

    __tablename__ = "produto"
    __table_args__ = {"extend_existing": True}

    id_produto: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome: Mapped[str | None] = mapped_column(String(255))
    preco: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
