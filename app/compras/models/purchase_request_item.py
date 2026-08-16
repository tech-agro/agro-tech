from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class PurchaseRequestItemModel(Base):
    __tablename__ = "item_solicitacao_compra"

    id_item: Mapped[int] = mapped_column(primary_key=True)
    id_solicitacao: Mapped[int] = mapped_column(
        ForeignKey("solicitacao_compra.id_solicitacao"), nullable=False
    )
    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produto.id_produto"), nullable=False
    )
    quantidade: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
