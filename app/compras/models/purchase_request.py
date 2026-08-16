from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.compras.enum import PurchaseRequestStatus, PurchaseType
from app.core.base import Base


class PurchaseRequestModel(Base):
    __tablename__ = "solicitacao_compra"

    id_solicitacao: Mapped[int] = mapped_column(primary_key=True)
    data_solicitacao: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[PurchaseRequestStatus] = mapped_column(
        Enum(
            PurchaseRequestStatus,
            name="status_solicitacao_compra_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    tipo_compra: Mapped[PurchaseType] = mapped_column(
        Enum(
            PurchaseType,
            name="tipo_compra_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    observacao: Mapped[str | None] = mapped_column(Text)
    id_tipo_maquina: Mapped[int | None] = mapped_column(
        ForeignKey("tipo_maquina.id_tipo_maquina")
    )
    patrimonio: Mapped[str | None] = mapped_column(String(80))
    id_fazenda: Mapped[int | None] = mapped_column(ForeignKey("fazenda.id_fazenda"))
