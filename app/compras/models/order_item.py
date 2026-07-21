from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class OrderItemModel(Base):
    __tablename__ = "item_pedido"

    id_item: Mapped[int] = mapped_column(primary_key=True)
    id_pedido: Mapped[int] = mapped_column(
        ForeignKey("pedido.id_pedido"), nullable=False
    )
    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produto.id_produto"), nullable=False
    )
    quantidade: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    valor_unitario: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
