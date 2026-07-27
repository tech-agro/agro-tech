"""Modelo ORM da entidade plano_manutencao."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.manutencao.models.maquina import MaquinaModel
    from app.manutencao.models.manutencao_preventiva import ManutencaoPreventivaModel


class PlanoManutencaoModel(Base):
    """Representa um plano de manutenção preventiva para uma máquina.

    Corresponde à tabela `plano_manutencao` no banco.
    """

    __tablename__ = "plano_manutencao"

    id_plano: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    id_maquina: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("maquina.id_maquina"),
        nullable=False,
        index=True,
    )

    periodicidade: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    proxima_execucao: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relacionamentos
    maquina: Mapped["MaquinaModel"] = relationship(
        back_populates="planos_manutencao",
    )

    manutencoes_preventivas: Mapped[list["ManutencaoPreventivaModel"]] = (
        relationship(
            back_populates="plano",
        )
    )

    def __repr__(self) -> str:
        return (
            f"<PlanoManutencaoModel "
            f"id={self.id_plano} "
            f"id_maquina={self.id_maquina}>"
        )
