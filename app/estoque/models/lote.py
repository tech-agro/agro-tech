"""Modelo ORM da entidade lote."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.estoque.enum import LotOriginType, StatusLote


class LoteModel(Base):
    """Product lot used for agricultural traceability (harvest, purchase, etc.)."""

    __tablename__ = "lote"
    __table_args__ = {"extend_existing": True}

    id_lote: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    id_colheita: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("colheita.id_colheita"),
        index=True,
    )

    id_produto: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("produto.id_produto"),
        nullable=False,
        index=True,
    )

    codigo_lote: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    validade: Mapped[date | None] = mapped_column(Date)

    qualidade: Mapped[str | None] = mapped_column(String(80))

    status: Mapped[StatusLote] = mapped_column(
        Enum(
            StatusLote,
            name="status_lote_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=StatusLote.LIBERADO,
        server_default=StatusLote.LIBERADO.value,
    )

    tipo_origem: Mapped[LotOriginType] = mapped_column(
        Enum(
            LotOriginType,
            name="tipo_origem_lote_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=LotOriginType.COMPRA,
    )

    quantidade_inicial: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    def __repr__(self) -> str:
        return f"<LoteModel id={self.id_lote} codigo={self.codigo_lote!r}>"
