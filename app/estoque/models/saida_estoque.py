"""Modelo ORM da entidade saida_estoque."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel


class SaidaEstoqueModel(Base):
    """Representa a saída de produto do estoque para uso em uma atividade agrícola.

    Corresponde à tabela `saida_estoque` no banco.
    """

    __tablename__ = "saida_estoque"

    id_saida: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_movimentacao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("movimentacao_estoque.id_movimentacao"),
        nullable=False,
        unique=True,
    )

    id_atividade: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("atividade_agricola.id_atividade"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<SaidaEstoqueModel "
            f"id={self.id_saida} "
            f"id_movimentacao={self.id_movimentacao} "
            f"id_atividade={self.id_atividade}>"
        )