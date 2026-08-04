from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.logistica.enum import LocationType


class LogisticsLocationModel(Base):
    __tablename__ = "local_logistico"

    id_local_logistico: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[LocationType] = mapped_column(
        Enum(
            LocationType,
            name="tipo_local_logistico_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    id_endereco: Mapped[int | None] = mapped_column(
        ForeignKey("endereco.id_endereco")
    )
    id_local_armazenamento: Mapped[int | None] = mapped_column(
        ForeignKey("local_armazenamento.id_local")
    )
    id_local_armazenamento: Mapped[int | None] = mapped_column(
        ForeignKey("local_armazenamento.id_local")
    )
