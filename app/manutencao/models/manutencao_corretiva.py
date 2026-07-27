"""Modelo ORM da entidade manutencao_corretiva."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.manutencao.models.manutencao import ManutencaoModel


class ManutencaoCorretivaModel(Base):
    """Detalhes de uma manutenção corretiva.

    Corresponde à tabela `manutencao_corretiva` no banco.
    """

    __tablename__ = "manutencao_corretiva"

    id_manutencao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("manutencao.id_manutencao"),
        primary_key=True,
    )

    defeito_relatado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    causa_raiz: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    solucao_aplicada: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relacionamentos
    manutencao: Mapped["ManutencaoModel"] = relationship(
        back_populates="corretiva",
    )

    def __repr__(self) -> str:
        return (
            f"<ManutencaoCorretivaModel "
            f"id_manutencao={self.id_manutencao}>"
        )
