"""Modelo ORM da entidade abastecimento."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.maquina import MaquinaModel


class AbastecimentoModel(Base):
    """Representa um abastecimento realizado em uma máquina.

    Corresponde à tabela `abastecimento` no banco.
    """

    __tablename__ = "abastecimento"

    id_abastecimento: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    id_maquina: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("maquina.id_maquina"),
        nullable=False,
        index=True,
    )

    combustivel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    litros: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    valor: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    horimetro: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    dt_abastecimento: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # Relacionamentos
    maquina: Mapped["MaquinaModel"] = relationship(
        back_populates="abastecimentos"
    )

    def __repr__(self) -> str:
        return (
            f"<AbastecimentoModel "
            f"id={self.id_abastecimento} "
            f"id_maquina={self.id_maquina}>"
        )