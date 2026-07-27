from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.logistica.enum import OperationStatus, OperationType


class OperationModel(Base):
    __tablename__ = "operacao_logistica"

    id_operacao: Mapped[int] = mapped_column(primary_key=True)
    id_veiculo: Mapped[int] = mapped_column(
        ForeignKey("veiculo.id_veiculo"), nullable=False
    )
    id_origem: Mapped[int] = mapped_column(
        ForeignKey("local_logistico.id_local_logistico"), nullable=False
    )
    id_destino: Mapped[int] = mapped_column(
        ForeignKey("local_logistico.id_local_logistico"), nullable=False
    )
    id_venda: Mapped[int | None] = mapped_column(ForeignKey("venda.id_venda"))
    tipo: Mapped[OperationType] = mapped_column(
        Enum(
            OperationType,
            name="tipo_operacao_logistica_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=OperationType.VENDA,
    )
    custo_previsto: Mapped[float | None] = mapped_column(Numeric(14, 2))
    data_inicio: Mapped[datetime | None] = mapped_column(DateTime)
    data_fim: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[OperationStatus] = mapped_column(
        Enum(
            OperationStatus,
            name="status_operacao_logistica_enum",
            create_type=False,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
