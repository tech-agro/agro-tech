"""Modelo ORM da entidade recebimento_compra."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.estoque import EstoqueModel
    from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel


class RecebimentoCompraModel(Base):
    """Representa o recebimento físico (conferência) de um item de compra no estoque.

    Corresponde à tabela `recebimento_compra` no banco.
    """

    __tablename__ = "recebimento_compra"
    __table_args__ = (
        CheckConstraint("quantidade_recebida > 0", name="chk_recebimento_quantidade_pos"),
    )

    id_recebimento: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_item_pedido: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("item_pedido.id_item"), nullable=False, index=True
    )
    id_estoque: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("estoque.id_estoque"), nullable=False, index=True
    )
    id_movimentacao: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movimentacao_estoque.id_movimentacao"), nullable=False, unique=True
    )
    quantidade_recebida: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    data_recebimento: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<RecebimentoCompraModel id={self.id_recebimento} "
            f"id_item_pedido={self.id_item_pedido} id_estoque={self.id_estoque}>"
        )