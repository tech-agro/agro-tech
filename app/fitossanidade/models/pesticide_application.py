from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class PesticideApplicationModel(Base):
    __tablename__ = "aplicacao_defensivo"
    __table_args__ = {"extend_existing": True}

    id_aplicacao: Mapped[int] = mapped_column(primary_key=True)
    id_controle: Mapped[int] = mapped_column(
        ForeignKey("controle_fitossanitario.id_controle"), nullable=False
    )
    id_insumo: Mapped[int] = mapped_column(
        ForeignKey("insumo.id_produto"), nullable=False
    )
    dose_hectare: Mapped[float | None] = mapped_column(Numeric(12, 2))
    volume_aplicado: Mapped[float | None] = mapped_column(Numeric(12, 2))
    dt_aplicacao: Mapped[date | None] = mapped_column(Date)
    dt_carencia: Mapped[date | None] = mapped_column(Date)
    id_maquina: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("maquina.id_maquina")
    )
    id_estoque_saida: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("estoque.id_estoque")
    )
    id_lote_saida: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("lote.id_lote")
    )
