"""Modelo ORM da entidade lote."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.estoque.enum import StatusLote

if TYPE_CHECKING:
    from app.estoque.models.certificacao_lote import CertificacaoLoteModel
    from app.estoque.models.consumo_insumo import ConsumoInsumoModel
    from app.estoque.models.movimentacao_estoque import MovimentacaoEstoqueModel


class LoteModel(Base):
    """Representa um lote de produto originado de uma colheita.

    Corresponde à tabela `lote` no banco.
    """

    __tablename__ = "lote"

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

    def __repr__(self) -> str:
        return f"<LoteModel id={self.id_lote} codigo={self.codigo_lote!r}>"