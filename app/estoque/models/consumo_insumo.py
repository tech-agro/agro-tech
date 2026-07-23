"""Modelo ORM da entidade consumo_insumo."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.lote import LoteModel


class ConsumoInsumoModel(Base):
    """Representa o consumo de um insumo (de um lote específico) em uma atividade agrícola.

    Corresponde à tabela `consumo_insumo` no banco.
    """

    __tablename__ = "consumo_insumo"

    __table_args__ = (
        CheckConstraint(
            "quantidade > 0",
            name="chk_consumo_insumo_quantidade_pos",
        ),
    )

    id_atividade: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("atividade_agricola.id_atividade"),
        primary_key=True,
    )

    id_insumo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("insumo.id_produto"),
        primary_key=True,
    )

    id_lote: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("lote.id_lote"),
        primary_key=True,
    )

    quantidade: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    # Relacionamentos
    lote: Mapped["LoteModel"] = relationship(back_populates="consumos_insumo")

    def __repr__(self) -> str:
        return (
            f"<ConsumoInsumoModel "
            f"id_atividade={self.id_atividade} "
            f"id_insumo={self.id_insumo} "
            f"id_lote={self.id_lote} "
            f"quantidade={self.quantidade}>"
        )