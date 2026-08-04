from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class PestModel(Base):
    __tablename__ = "praga"

    id_agente: Mapped[int] = mapped_column(
        ForeignKey("agente_nocivo.id_agente"), primary_key=True
    )
    tipo_praga: Mapped[str | None] = mapped_column(String(80))
    habito_alimentar: Mapped[str | None] = mapped_column(String(120))
