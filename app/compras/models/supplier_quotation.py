from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.compras.enum import QuotationStatus
from app.core.base import Base


class SupplierQuotationModel(Base):
    __tablename__ = "cotacao_compra"

    id_cotacao: Mapped[int] = mapped_column(primary_key=True)
    id_solicitacao: Mapped[int] = mapped_column(
        ForeignKey("solicitacao_compra.id_solicitacao"), nullable=False
    )
    id_fornecedor: Mapped[int] = mapped_column(
        ForeignKey("fornecedor.id_fornecedor"), nullable=False
    )
    status: Mapped[QuotationStatus] = mapped_column(
        Enum(
            QuotationStatus,
            name="status_cotacao_compra_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    prazo_entrega_dias: Mapped[int | None] = mapped_column(Integer)
    observacao: Mapped[str | None] = mapped_column(Text)
