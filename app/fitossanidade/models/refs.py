"""Minimal ORM stubs so SQLAlchemy can resolve FKs and read labels.

Full ownership of these tables belongs to other modules; phytosanitary only
registers enough metadata for FK integrity and UI lookups.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class PessoaRef(Base):
    __tablename__ = "pessoa"
    __table_args__ = {"extend_existing": True}

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


class FuncionarioRef(Base):
    __tablename__ = "funcionario"
    __table_args__ = {"extend_existing": True}

    id_funcionario: Mapped[int] = mapped_column(primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(100))
    setor: Mapped[str | None] = mapped_column(String(100))


class PlantioRef(Base):
    __tablename__ = "plantio"
    __table_args__ = {"extend_existing": True}

    id_plantio: Mapped[int] = mapped_column(primary_key=True)
    id_produto: Mapped[int] = mapped_column(ForeignKey("produto.id_produto"), nullable=False)
    dt_plantio: Mapped[date | None] = mapped_column(Date)


class ProdutoRef(Base):
    __tablename__ = "produto"
    __table_args__ = {"extend_existing": True}

    id_produto: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)


class InsumoRef(Base):
    __tablename__ = "insumo"
    __table_args__ = {"extend_existing": True}

    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produto.id_produto"), primary_key=True
    )
    classe_agronomica: Mapped[str | None] = mapped_column(String(120))
    principio_ativo: Mapped[str | None] = mapped_column(String(120))
    periodo_carencia_dias: Mapped[int | None] = mapped_column(Integer)
    registro_mapa: Mapped[str | None] = mapped_column(String(120))


class MaquinaRef(Base):
    __tablename__ = "maquina"
    __table_args__ = {"extend_existing": True}

    id_maquina: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
