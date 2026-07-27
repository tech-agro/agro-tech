from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class HarmfulAgentModel(Base):
    __tablename__ = "agente_nocivo"

    id_agente: Mapped[int] = mapped_column(primary_key=True)
    nome_comum: Mapped[str | None] = mapped_column(String(120))
    nome_cientifico: Mapped[str | None] = mapped_column(String(120))
