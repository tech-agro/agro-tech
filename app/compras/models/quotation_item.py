from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class QuotationItemModel(Base):
    __tablename__ = "item_cotacao_compra"

    id_item_cotacao: Mapped[int] = mapped_column(primary_key=True)
    id_cotacao: Mapped[int] = mapped_column(
        ForeignKey("cotacao_compra.id_cotacao"), nullable=False
    )
    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produto.id_produto"), nullable=False
    )
    quantidade: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
