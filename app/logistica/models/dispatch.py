from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.logistica.enum import DispatchStatus


class DispatchModel(Base):
    __tablename__ = "expedicao"

    id_expedicao: Mapped[int] = mapped_column(primary_key=True)
    id_carga: Mapped[int] = mapped_column(
        ForeignKey("carga.id_carga"), nullable=False, unique=True
    )
    data_saida: Mapped[datetime | None] = mapped_column(DateTime)
    data_chegada_prevista: Mapped[datetime | None] = mapped_column(DateTime)
    data_entrega: Mapped[datetime | None] = mapped_column(DateTime)
    id_funcionario: Mapped[int | None] = mapped_column(
        ForeignKey("funcionario.id_funcionario")
    )
    observacoes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DispatchStatus] = mapped_column(
        Enum(
            DispatchStatus,
            name="status_expedicao_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
