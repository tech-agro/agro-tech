"""Modelo ORM da entidade saldo_estoque."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.estoque import EstoqueModel


class SaldoEstoqueModel(Base):
    """Representa o saldo consolidado (quantidade atual) de um produto
    dentro de um estoque específico.

    Corresponde à tabela `saldo_estoque` no banco.
    """

    __tablename__ = "saldo_estoque"

    __table_args__ = (
        UniqueConstraint(
            "id_estoque",
            "id_produto",
            name="uq_saldo_estoque_produto",
        ),
        CheckConstraint(
            "quantidade_atual >= 0",
            name="chk_saldo_quantidade_pos",
        ),
    )

    id_saldo: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_estoque: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("estoque.id_estoque"),
        nullable=False,
    )

    id_produto: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("produto.id_produto"),
        nullable=False,
        index=True,
    )

    quantidade_atual: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Relacionamentos
    estoque: Mapped["EstoqueModel"] = relationship(back_populates="saldos")

    def __repr__(self) -> str:
        return (
            f"<SaldoEstoqueModel "
            f"id={self.id_saldo} "
            f"id_estoque={self.id_estoque} "
            f"id_produto={self.id_produto} "
            f"quantidade_atual={self.quantidade_atual}>"
        )