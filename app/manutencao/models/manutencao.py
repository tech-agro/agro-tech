"""Modelo ORM da entidade manutencao."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.manutencao.models.maquina import MaquinaModel
    from app.manutencao.models.manutencao_corretiva import ManutencaoCorretivaModel
    from app.manutencao.models.manutencao_preventiva import ManutencaoPreventivaModel
    from app.manutencao.models.ordem_servico import OrdemServicoModel
    from app.manutencao.models.prestador_servico import PrestadorServicoModel


class ManutencaoModel(Base):
    """Representa uma manutenção realizada em uma máquina.

    Corresponde à tabela `manutencao` no banco.
    """

    __tablename__ = "manutencao"

    id_manutencao: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    id_maquina: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("maquina.id_maquina"),
        nullable=False,
        index=True,
    )

    id_funcionario: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("funcionario.id_funcionario"),
        nullable=True,
    )

    id_prestador: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("prestador_servico.id_prestador"),
        nullable=True,
        index=True,
    )

    tipo: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    custo: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    dt_inicio: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    dt_fim: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relacionamentos
    maquina: Mapped["MaquinaModel"] = relationship(
        back_populates="manutencoes",
    )

    prestador: Mapped["PrestadorServicoModel | None"] = relationship(
        back_populates="manutencoes",
    )

    ordens_servico: Mapped[list["OrdemServicoModel"]] = relationship(
        back_populates="manutencao",
    )

    preventiva: Mapped["ManutencaoPreventivaModel | None"] = relationship(
        back_populates="manutencao",
        uselist=False,
    )

    corretiva: Mapped["ManutencaoCorretivaModel | None"] = relationship(
        back_populates="manutencao",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ManutencaoModel "
            f"id={self.id_manutencao} "
            f"id_maquina={self.id_maquina} "
            f"status={self.status!r}>"
        )
