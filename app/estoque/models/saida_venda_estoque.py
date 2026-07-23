"""Modelo ORM da entidade saida_venda_estoque."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel


class SaidaVendaEstoqueModel(Base):
    """Representa a saída de produto do estoque por motivo de venda.

    Corresponde à tabela `saida_venda_estoque` no banco.
    """

    __tablename__ = "saida_venda_estoque"

    id_saida_venda: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_movimentacao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("movimentacao_estoque.id_movimentacao"),
        nullable=False,
        unique=True,
    )

    id_item_venda: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("item_venda.id_item_venda"),
        nullable=False,
        index=True,
    )

    # Relacionamentos
    movimentacao: Mapped["MovimentacaoEstoqueModel"] = relationship(back_populates="saida_venda")

    def __repr__(self) -> str:
        return (
            f"<SaidaVendaEstoqueModel "
            f"id={self.id_saida_venda} "
            f"id_movimentacao={self.id_movimentacao} "
            f"id_item_venda={self.id_item_venda}>"
        )