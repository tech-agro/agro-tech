"""Stubs ORM minimos para tabelas de producao usadas em consultas de BI.

O modulo producao gerencia talhao/safra/planejamento_safra/plantio/colheita
via SQLAlchemy Core + modelos Pydantic (nao ORM), entao inteligencia declara
aqui o mapeamento minimo necessario para montar joins de agregacao com a
mesma Session compartilhada (mesmo banco, mesma `Base.metadata`).
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class SafraRef(Base):
    """Stub minimo da tabela safra (modulo producao)."""

    __tablename__ = "safra"
    __table_args__ = {"extend_existing": True}

    id_safra: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)


class TalhaoRef(Base):
    """Stub minimo da tabela talhao (modulo producao)."""

    __tablename__ = "talhao"
    __table_args__ = {"extend_existing": True}

    id_talhao: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_safra: Mapped[int] = mapped_column(BigInteger, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    area_hectares: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


class PlanejamentoSafraRef(Base):
    """Stub minimo da tabela planejamento_safra (modulo producao)."""

    __tablename__ = "planejamento_safra"
    __table_args__ = {"extend_existing": True}

    id_planejamento: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_safra: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_talhao: Mapped[int] = mapped_column(BigInteger, nullable=False)
    id_cultura: Mapped[int] = mapped_column(BigInteger, nullable=False)
    meta_produtividade: Mapped[float | None] = mapped_column(Numeric(12, 2))
    area_planejada: Mapped[float | None] = mapped_column(Numeric(12, 2))


class CulturaRef(Base):
    """Stub minimo da tabela cultura (modulo producao)."""

    __tablename__ = "cultura"
    __table_args__ = {"extend_existing": True}

    id_cultura: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)


class PlantioRef(Base):
    """Stub minimo da tabela plantio (modulo producao)."""

    __tablename__ = "plantio"
    __table_args__ = {"extend_existing": True}

    id_plantio: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_talhao: Mapped[int] = mapped_column(BigInteger, nullable=False)


class ColheitaRef(Base):
    """Stub minimo da tabela colheita (modulo producao)."""

    __tablename__ = "colheita"
    __table_args__ = {"extend_existing": True}

    id_colheita: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_plantio: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantidade_colhida: Mapped[float | None] = mapped_column(Numeric(12, 2))
