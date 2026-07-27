"""Modelos ORM do dominio inteligencia."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


class IndicadorModel(Base):
    """Representa um indicador (KPI) monitorado pelo modulo de inteligencia.

    Corresponde a tabela `indicador` no banco.
    """

    __tablename__ = "indicador"

    id_indicador: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    nome: Mapped[str] = mapped_column(String(120), nullable=False)

    unidade: Mapped[str | None] = mapped_column(String(30))

    medicoes: Mapped[list["MedicaoIndicadorModel"]] = relationship(
        back_populates="indicador",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<IndicadorModel id={self.id_indicador} nome={self.nome!r}>"


class MedicaoIndicadorModel(Base):
    """Registro de valor medido de um indicador em uma safra.

    Corresponde a tabela `medicao_indicador` no banco.
    """

    __tablename__ = "medicao_indicador"

    id_medicao: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    id_indicador: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("indicador.id_indicador"),
        nullable=False,
        index=True,
    )

    id_safra: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("safra.id_safra"),
        nullable=False,
        index=True,
    )

    valor: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    data_referencia: Mapped[date | None] = mapped_column(Date)

    indicador: Mapped[IndicadorModel] = relationship(back_populates="medicoes")

    def __repr__(self) -> str:
        return (
            f"<MedicaoIndicadorModel id={self.id_medicao} "
            f"indicador={self.id_indicador} safra={self.id_safra}>"
        )
