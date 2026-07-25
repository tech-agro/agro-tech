"""Modelo ORM da entidade local_armazenamento."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.estoque import EstoqueModel


class LocalArmazenamentoModel(Base):
    """Representa um local físico de armazenamento (armazém, silo, câmara, etc.).

    Corresponde à tabela `local_armazenamento` no banco.
    """

    __tablename__ = "local_armazenamento"

    __table_args__ = (
        CheckConstraint(
            "capacidade IS NULL OR capacidade > 0",
            name="chk_local_capacidade_pos",
        ),
    )

    id_local: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    descricao: Mapped[str] = mapped_column(String(255), nullable=False)

    capacidade: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    def __repr__(self) -> str:
        return (
            f"<LocalArmazenamentoModel "
            f"id={self.id_local} "
            f"descricao={self.descricao!r}>"
        )