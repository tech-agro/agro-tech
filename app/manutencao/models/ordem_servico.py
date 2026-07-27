"""Modelo ORM da entidade ordem_servico."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.manutencao.models.manutencao import ManutencaoModel


class OrdemServicoModel(Base):
    """Representa uma ordem de serviço vinculada a uma manutenção.

    Corresponde à tabela `ordem_servico` no banco.
    """

    __tablename__ = "ordem_servico"

    id_ordem_servico: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    id_manutencao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("manutencao.id_manutencao"),
        nullable=False,
        index=True,
    )

    descricao: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Relacionamentos
    manutencao: Mapped["ManutencaoModel"] = relationship(
        back_populates="ordens_servico",
    )

    def __repr__(self) -> str:
        return (
            f"<OrdemServicoModel "
            f"id={self.id_ordem_servico} "
            f"id_manutencao={self.id_manutencao} "
            f"status={self.status!r}>"
        )
