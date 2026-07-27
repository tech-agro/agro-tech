"""Minimal ORM stubs so SQLAlchemy can resolve FKs and read labels.

Full ownership of these tables belongs to other modules; logistics only
registers enough metadata for FK integrity and UI lookups.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class ClienteRef(Base):
    __tablename__ = "cliente"
    __table_args__ = {"extend_existing": True}

    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"), nullable=False)


class PessoaRef(Base):
    __tablename__ = "pessoa"
    __table_args__ = {"extend_existing": True}

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


class VendaRef(Base):
    __tablename__ = "venda"
    __table_args__ = {"extend_existing": True}

    id_venda: Mapped[int] = mapped_column(primary_key=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"), nullable=False)
    valor_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    data_venda: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(40))


class ProdutoRef(Base):
    __tablename__ = "produto"
    __table_args__ = {"extend_existing": True}

    id_produto: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


class LoteRef(Base):
    __tablename__ = "lote"
    __table_args__ = {"extend_existing": True}

    id_lote: Mapped[int] = mapped_column(primary_key=True)
    id_produto: Mapped[int] = mapped_column(ForeignKey("produto.id_produto"), nullable=False)
    codigo_lote: Mapped[str] = mapped_column(String(120), nullable=False)


class FuncionarioRef(Base):
    __tablename__ = "funcionario"
    __table_args__ = {"extend_existing": True}

    id_funcionario: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(100))
    setor: Mapped[str | None] = mapped_column(String(100))

