"""Modelo ORM da entidade maquina."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.estoque.models.abastecimento import AbastecimentoModel
    from app.estoque.models.manutencao import ManutencaoModel
    from app.estoque.models.tipo_maquina import TipoMaquinaModel
    from app.estoque.models.uso_maquina import UsoMaquinaModel


class MaquinaModel(Base):
    """Representa uma máquina.

    Corresponde à tabela `maquina` no banco.
    """

    __tablename__ = "maquina"

    id_maquina: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    id_tipo_maquina: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tipo_maquina.id_tipo_maquina"),
        nullable=False,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Relacionamentos
    tipo_maquina: Mapped["TipoMaquinaModel"] = relationship(
        back_populates="maquinas"
    )

    usos: Mapped[list["UsoMaquinaModel"]] = relationship(
        back_populates="maquina"
    )

    abastecimentos: Mapped[list["AbastecimentoModel"]] = relationship(
        back_populates="maquina"
    )

    manutencoes: Mapped[list["ManutencaoModel"]] = relationship(
        back_populates="maquina"
    )

    def __repr__(self) -> str:
        return (
            f"<MaquinaModel "
            f"id={self.id_maquina} "
            f"nome={self.nome!r} "
            f"status={self.status!r}>"
        )