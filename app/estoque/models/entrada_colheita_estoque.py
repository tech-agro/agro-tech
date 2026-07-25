"""Modelo ORM da entidade entrada_colheita_estoque."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class EntradaColheitaEstoqueModel(Base):
    """Representa a entrada de produto em estoque originada de uma colheita.

    Corresponde à tabela `entrada_colheita_estoque` no banco.
    """

    __tablename__ = "entrada_colheita_estoque"

    id_entrada_colheita: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_colheita: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("colheita.id_colheita"), nullable=False, index=True
    )
    id_movimentacao: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movimentacao_estoque.id_movimentacao"), nullable=False, unique=True
    )

    def __repr__(self) -> str:
        return (
            f"<EntradaColheitaEstoqueModel id={self.id_entrada_colheita} "
            f"id_colheita={self.id_colheita} id_movimentacao={self.id_movimentacao}>"
        )