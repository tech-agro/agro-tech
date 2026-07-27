from __future__ import annotations

from sqlalchemy import Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.logistica.enum import VehicleType


class VehicleModel(Base):
    __tablename__ = "veiculo"

    id_veiculo: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[VehicleType] = mapped_column(
        Enum(
            VehicleType,
            name="tipo_veiculo_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    placa: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    capacidade: Mapped[float | None] = mapped_column(Numeric(12, 2))
