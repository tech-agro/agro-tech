from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class PurchaseModel(Base):
    __tablename__ = "compra"

    id_compra: Mapped[int] = mapped_column(primary_key=True)
    id_pedido: Mapped[int] = mapped_column(
        ForeignKey("pedido.id_pedido"), nullable=False
    )
    id_centro_custo: Mapped[int] = mapped_column(
        ForeignKey("centro_custo.id_centro_custo"), nullable=False
    )
    valor_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    data_compra: Mapped[date | None] = mapped_column(Date)
