"""Modelo ORM da entidade certificacao_lote."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, String, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.core.enum import StatusCertificacao

if TYPE_CHECKING:
    from app.estoque.models.lote import LoteModel


class CertificacaoLoteModel(Base):
    """Representa a certificação (orgânica, rastreabilidade, etc.) emitida para um lote.

    Um lote pode ter várias certificações associadas.

    Corresponde à tabela `certificacao_lote` no banco.
    """

    __tablename__ = "certificacao_lote"

    __table_args__ = (
        CheckConstraint(
            "dt_validade IS NULL OR dt_emissao IS NULL OR dt_validade >= dt_emissao",
            name="chk_certificacao_lote_periodo",
        ),
        UniqueConstraint(
            "id_certificacao",
            "id_lote",
            name="uq_certificacao_lote",
        ),
    )

    id_cert_lote: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    id_certificacao: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("certificacao.id_certificacao"),
        nullable=False,
    )

    id_lote: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("lote.id_lote"),
        nullable=False,
        index=True,
    )

    dt_emissao: Mapped[date | None] = mapped_column(Date)

    dt_validade: Mapped[date | None] = mapped_column(Date)

    numero_certificado: Mapped[str | None] = mapped_column(String(120), unique=True)
    
    status: Mapped[StatusCertificacao] = mapped_column(
        Enum(StatusCertificacao, name="status_certificacao_enum", create_type=False),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CertificacaoLoteModel id={self.id_cert_lote} id_lote={self.id_lote} status={self.status!r}>"