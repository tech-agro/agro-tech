"""Modelo ORM da entidade entrada_estoque."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel


class EntradaEstoqueModel(Base):
    """Representa a entrada de produto em estoque originada de uma compra.

    Corresponde à tabela `entrada_estoque` no banco.
    """

    __tablename__ = "entrada_estoque"

    id_entrada: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    id_compra: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("compra.id_compra"),
        nullable=False,
    )

    id_movimentacao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("movimentacao_estoque.id_movimentacao"),
        nullable=False,
        unique=True,
    )

    # Relacionamentos
    movimentacao: Mapped["MovimentacaoEstoqueModel"] = relationship(
        back_populates="entrada"
    )

    def __repr__(self) -> str:
        return (
            f"<EntradaEstoqueModel "
            f"id={self.id_entrada} "
            f"id_compra={self.id_compra} "
            f"id_movimentacao={self.id_movimentacao}>"
        )