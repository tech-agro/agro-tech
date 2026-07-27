from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class ControlModel(Base):
    __tablename__ = "controle_fitossanitario"

    id_controle: Mapped[int] = mapped_column(primary_key=True)
    id_plantio: Mapped[int] = mapped_column(
        ForeignKey("plantio.id_plantio"), nullable=False
    )
    id_funcionario: Mapped[int] = mapped_column(
        ForeignKey("funcionario.id_funcionario"), nullable=False
    )
    dt_identificacao: Mapped[date | None] = mapped_column(Date)
    nivel_severidade: Mapped[str | None] = mapped_column(String(50))
    area_afetada_hectares: Mapped[float | None] = mapped_column(Numeric(12, 2))
    recomendacao: Mapped[str | None] = mapped_column(Text)
