from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class WeighingModel(Base):
    __tablename__ = "pesagem"

    id_pesagem: Mapped[int] = mapped_column(primary_key=True)
    id_carga: Mapped[int] = mapped_column(ForeignKey("carga.id_carga"), nullable=False)
    peso_registrado: Mapped[float | None] = mapped_column(Numeric(12, 2))
    data_pesagem: Mapped[datetime | None] = mapped_column(DateTime)
