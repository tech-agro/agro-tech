from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class EquipmentPurchaseDetailModel(Base):
    __tablename__ = "detalhe_compra_equipamento"

    id_pedido: Mapped[int] = mapped_column(
        ForeignKey("pedido.id_pedido"), primary_key=True
    )
    id_tipo_maquina: Mapped[int] = mapped_column(
        ForeignKey("tipo_maquina.id_tipo_maquina"), nullable=False
    )
    patrimonio: Mapped[str | None] = mapped_column(String(80))
    id_fazenda: Mapped[int] = mapped_column(
        ForeignKey("fazenda.id_fazenda"), nullable=False
    )
    id_maquina: Mapped[int | None] = mapped_column(ForeignKey("maquina.id_maquina"))
