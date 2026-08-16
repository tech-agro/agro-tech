from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class PurchaseInvoiceModel(Base):
    __tablename__ = "nota_fiscal_compra"

    id_nota_fiscal: Mapped[int] = mapped_column(primary_key=True)
    id_pedido: Mapped[int] = mapped_column(
        ForeignKey("pedido.id_pedido"), nullable=False
    )
    id_fornecedor: Mapped[int] = mapped_column(
        ForeignKey("fornecedor.id_fornecedor"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(30), nullable=False)
    serie: Mapped[str] = mapped_column(String(10), nullable=False)
    data_emissao: Mapped[date] = mapped_column(Date, nullable=False)
    valor_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    chave_acesso: Mapped[str | None] = mapped_column(String(44))
