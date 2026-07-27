from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CHAR, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class AddressModel(Base):
    __tablename__ = "endereco"

    id_endereco: Mapped[int] = mapped_column(primary_key=True)
    logradouro: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[str | None] = mapped_column(String(30))
    cidade: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    cep: Mapped[str | None] = mapped_column(String(12))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
