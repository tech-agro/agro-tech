"""Minimal ORM stubs so SQLAlchemy can resolve FKs and read labels.

Full ownership of these tables belongs to other modules; purchases only
registers enough metadata for FK integrity and UI lookups.
"""

from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.comercial.enum import UnitSymbol
from app.core.base import Base


class PessoaRef(Base):
    __tablename__ = "pessoa"
    __table_args__ = {"extend_existing": True}

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    documento: Mapped[str] = mapped_column(String(50), nullable=False)


class FornecedorRef(Base):
    __tablename__ = "fornecedor"
    __table_args__ = {"extend_existing": True}

    id_fornecedor: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(100))


class UnidadeMedidaRef(Base):
    __tablename__ = "unidade_medida"
    __table_args__ = {"extend_existing": True}

    id_unidade: Mapped[int] = mapped_column(primary_key=True)
    sigla: Mapped[UnitSymbol] = mapped_column(
        Enum(
            UnitSymbol,
            name="unidade_sigla_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        unique=True,
    )
    descricao: Mapped[str] = mapped_column(String(120), nullable=False)


class ProdutoRef(Base):
    __tablename__ = "produto"
    __table_args__ = {"extend_existing": True}

    id_produto: Mapped[int] = mapped_column(primary_key=True)
    id_unidade: Mapped[int] = mapped_column(
        ForeignKey("unidade_medida.id_unidade"), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


class CentroCustoRef(Base):
    __tablename__ = "centro_custo"
    __table_args__ = {"extend_existing": True}

    id_centro_custo: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
