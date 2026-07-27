"""ORM model for saldo_lote."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class SaldoLoteModel(Base):
    """Quantity on hand (and reserved) for a lot at a stock location."""

    __tablename__ = "saldo_lote"
    __table_args__ = (
        UniqueConstraint("id_estoque", "id_lote", name="saldo_lote_id_estoque_id_lote_key"),
        CheckConstraint("quantidade_atual >= 0", name="chk_saldo_lote_quantidade_pos"),
        CheckConstraint("quantidade_reservada >= 0", name="chk_saldo_lote_reservada_pos"),
        CheckConstraint(
            "quantidade_reservada <= quantidade_atual",
            name="chk_saldo_lote_reservada_lte_atual",
        ),
    )

    id_saldo_lote: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_estoque: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("estoque.id_estoque"), nullable=False
    )
    id_lote: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lote.id_lote"), nullable=False, index=True
    )
    quantidade_atual: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    quantidade_reservada: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0
    )
