"""Modelo ORM da entidade prestador_servico."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.manutencao.models.manutencao import ManutencaoModel


class PrestadorServicoModel(Base):
    """Representa um prestador de serviços.

    Corresponde à tabela `prestador_servico` no banco.
    """

    __tablename__ = "prestador_servico"

    id_prestador: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    nome: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    cnpj: Mapped[str] = mapped_column(
        String(18),
        unique=True,
        nullable=False,
    )

    especialidade: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    telefone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Relacionamentos
    manutencoes: Mapped[list["ManutencaoModel"]] = relationship(
        back_populates="prestador"
    )

    def __repr__(self) -> str:
        return (
            f"<PrestadorServicoModel "
            f"id={self.id_prestador} "
            f"nome={self.nome!r}>"
        )