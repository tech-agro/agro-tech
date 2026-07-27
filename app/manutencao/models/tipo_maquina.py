"""Modelo ORM da entidade tipo_maquina."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.manutencao.models.maquina import MaquinaModel


class TipoMaquinaModel(Base):
    """Representa um tipo de máquina.

    Corresponde à tabela `tipo_maquina` no banco.
    """

    __tablename__ = "tipo_maquina"

    id_tipo_maquina: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    descricao: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Relacionamentos
    maquinas: Mapped[list["MaquinaModel"]] = relationship(
        back_populates="tipo_maquina"
    )

    def __repr__(self) -> str:
        return (
            f"<TipoMaquinaModel "
            f"id={self.id_tipo_maquina} "
            f"descricao={self.descricao!r}>"
        )