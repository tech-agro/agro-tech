from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class LoadModel(Base):
    __tablename__ = "carga"

    id_carga: Mapped[int] = mapped_column(primary_key=True)
    id_operacao: Mapped[int] = mapped_column(
        ForeignKey("operacao_logistica.id_operacao"), nullable=False
    )
    id_lote: Mapped[int] = mapped_column(ForeignKey("lote.id_lote"), nullable=False)
    id_item_venda: Mapped[int | None] = mapped_column(ForeignKey("item_venda.id_item_venda"))
    quantidade: Mapped[float | None] = mapped_column(Numeric(12, 2))
    peso_previsto: Mapped[float | None] = mapped_column(Numeric(12, 2))
