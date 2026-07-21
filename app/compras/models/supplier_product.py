from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class SupplierProductModel(Base):
    """Auxiliary table; no public controller until the frontend needs it."""

    __tablename__ = "fornecedor_produto"

    id_fornecedor: Mapped[int] = mapped_column(
        ForeignKey("fornecedor.id_fornecedor"), primary_key=True
    )
    id_produto: Mapped[int] = mapped_column(
        ForeignKey("produto.id_produto"), primary_key=True
    )
    preco_referencia: Mapped[float | None] = mapped_column(Numeric(14, 2))
    prazo_entrega_dias: Mapped[int | None] = mapped_column(Integer)
