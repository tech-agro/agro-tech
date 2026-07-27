"""Minimal ORM stubs so SQLAlchemy can resolve FKs and read labels."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class ColheitaRef(Base):
    __tablename__ = "colheita"
    __table_args__ = {"extend_existing": True}

    id_colheita: Mapped[int] = mapped_column(primary_key=True)
    id_plantio: Mapped[int] = mapped_column(ForeignKey("plantio.id_plantio"), nullable=False)
    quantidade_colhida: Mapped[float | None] = mapped_column(Numeric(12, 2))
    dt_fim: Mapped[date | None] = mapped_column(Date)


class PlantioRef(Base):
    __tablename__ = "plantio"
    __table_args__ = {"extend_existing": True}

    id_plantio: Mapped[int] = mapped_column(primary_key=True)
    id_cultura: Mapped[int] = mapped_column(ForeignKey("cultura.id_cultura"), nullable=False)
    id_produto: Mapped[int] = mapped_column(ForeignKey("produto.id_produto"), nullable=False)


class CulturaRef(Base):
    __tablename__ = "cultura"
    __table_args__ = {"extend_existing": True}

    id_cultura: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)


class GraoRef(Base):
    __tablename__ = "grao"
    __table_args__ = {"extend_existing": True}

    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produto.id_produto"), primary_key=True
    )


class CertificacaoRef(Base):
    __tablename__ = "certificacao"
    __table_args__ = {"extend_existing": True}

    id_certificacao: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)


class ItemVendaRef(Base):
    """Estoque só precisa da PK para resolver a FK de `saida_venda_estoque`.

    `item_venda` é owned pelo módulo Comercial, que usa Pydantic + SQL puro
    (sem SQLAlchemy declarative) — este stub existe só para o SQLAlchemy
    conseguir montar a FK ao gravar uma saída por venda.
    """

    __tablename__ = "item_venda"
    __table_args__ = {"extend_existing": True}

    id_item_venda: Mapped[int] = mapped_column(primary_key=True)
