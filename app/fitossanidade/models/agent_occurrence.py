from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class AgentOccurrenceModel(Base):
    __tablename__ = "ocorrencia_agente"

    id_ocorrencia: Mapped[int] = mapped_column(primary_key=True)
    id_controle: Mapped[int] = mapped_column(
        ForeignKey("controle_fitossanitario.id_controle"), nullable=False
    )
    id_agente: Mapped[int] = mapped_column(
        ForeignKey("agente_nocivo.id_agente"), nullable=False
    )
    nivel_infestacao: Mapped[str | None] = mapped_column(String(50))
    metodo_controle: Mapped[str | None] = mapped_column(String(120))
