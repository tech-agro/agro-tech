"""Modelo ORM da entidade movimentacao_estoque."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.entrada_estoque import EntradaEstoqueModel
    from app.estoque.models.estoque import EstoqueModel
    from app.estoque.models.lote import LoteModel
    from app.estoque.models.saida_estoque import SaidaEstoqueModel
    from app.estoque.models.saida_venda_estoque import SaidaVendaEstoqueModel


class MovimentacaoEstoqueModel(Base):
    """Representa uma movimentação (entrada ou saída) de produto em um estoque.

    Corresponde à tabela `movimentacao_estoque` no banco.
    """

    __tablename__ = "movimentacao_estoque"

    __table_args__ = (
        CheckConstraint(
            "quantidade > 0",
            name="chk_movimentacao_quantidade_pos",
        ),
    )

    id_movimentacao: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_estoque: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("estoque.id_estoque"),
        nullable=False,
        index=True,
    )

    id_produto: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("produto.id_produto"),
        nullable=False,
        index=True,
    )

    id_lote: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("lote.id_lote"),
        index=True,
    )

    tipo_movimentacao: Mapped[str] = mapped_column(String(50), nullable=False)

    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    data_movimentacao: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relacionamentos
    estoque: Mapped["EstoqueModel"] = relationship(back_populates="movimentacoes")
    lote: Mapped["LoteModel"] = relationship(back_populates="movimentacoes")
    entrada: Mapped["EntradaEstoqueModel"] = relationship(back_populates="movimentacao", uselist=False)
    saida: Mapped["SaidaEstoqueModel"] = relationship(back_populates="movimentacao", uselist=False)
    saida_venda: Mapped["SaidaVendaEstoqueModel"] = relationship(back_populates="movimentacao", uselist=False)

    def __repr__(self) -> str:
        return (
            f"<MovimentacaoEstoqueModel "
            f"id={self.id_movimentacao} "
            f"tipo={self.tipo_movimentacao!r} "
            f"quantidade={self.quantidade}>"
        )