from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.compras.enum import OrderStatus, PurchaseType


class OrderModel(Base):
    __tablename__ = "pedido"

    id_pedido: Mapped[int] = mapped_column(primary_key=True)
    id_fornecedor: Mapped[int] = mapped_column(
        ForeignKey("fornecedor.id_fornecedor"), nullable=False
    )
    data_pedido: Mapped[date | None] = mapped_column(Date)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="status_pedido_compra_enum"),
        nullable=False,
    )
    id_solicitacao: Mapped[int | None] = mapped_column(
        ForeignKey("solicitacao_compra.id_solicitacao")
    )
    tipo_compra: Mapped[PurchaseType] = mapped_column(
        Enum(
            PurchaseType,
            name="tipo_compra_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=PurchaseType.INSUMO,
    )
