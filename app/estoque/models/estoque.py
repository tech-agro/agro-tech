"""Modelo ORM da entidade estoque."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.local_armazenamento import LocalArmazenamentoModel
    from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel
    from app.estoque.models.saldo_estoque import SaldoEstoqueModel


class EstoqueModel(Base):
    """Representa um estoque (categoria/controle de saldo) dentro de um local de armazenamento.

    Um mesmo local pode ter vários estoques (ex: insumos, peças de manutenção,
    grãos colhidos), cada um controlado separadamente.

    Corresponde à tabela `estoque` no banco.
    """

    __tablename__ = "estoque"

    id_estoque: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    id_local: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("local_armazenamento.id_local"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EstoqueModel id={self.id_estoque} id_local={self.id_local}>"