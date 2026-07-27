from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class DiseaseModel(Base):
    __tablename__ = "doenca"

    id_agente: Mapped[int] = mapped_column(
        ForeignKey("agente_nocivo.id_agente"), primary_key=True
    )
    agente_causador: Mapped[str | None] = mapped_column(String(120))
    sintomas: Mapped[str | None] = mapped_column(Text)
    condicao_favoravel: Mapped[str | None] = mapped_column(Text)
