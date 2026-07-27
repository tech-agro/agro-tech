"""Modelo ORM da entidade manutencao_preventiva."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.manutencao.models.manutencao import ManutencaoModel
    from app.manutencao.models.plano_manutencao import PlanoManutencaoModel


class ManutencaoPreventivaModel(Base):
    """Detalhes de uma manutenção preventiva.

    Corresponde à tabela `manutencao_preventiva` no banco.
    """

    __tablename__ = "manutencao_preventiva"

    id_manutencao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("manutencao.id_manutencao"),
        primary_key=True,
    )

    id_plano: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("plano_manutencao.id_plano"),
        nullable=False,
        index=True,
    )

    hodometro_execucao: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    proxima_hodometro: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    # Relacionamentos
    manutencao: Mapped["ManutencaoModel"] = relationship(
        back_populates="preventiva",
    )

    plano: Mapped["PlanoManutencaoModel"] = relationship(
        back_populates="manutencoes_preventivas",
    )

    def __repr__(self) -> str:
        return (
            f"<ManutencaoPreventivaModel "
            f"id_manutencao={self.id_manutencao} "
            f"id_plano={self.id_plano}>"
        )
