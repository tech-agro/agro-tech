"""Minimal ORM stubs so SQLAlchemy can resolve FKs and read labels.

Full ownership of these tables belongs to other módulos; o estoque só
registra os campos mínimos necessários para JOINs de exibição (rótulos).
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class CertificacaoRef(Base):
    __tablename__ = "certificacao"

    id_certificacao: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)