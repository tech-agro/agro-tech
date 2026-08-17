"""Schemas Pydantic do dominio inteligencia."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class IndicadorCreateSchema(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    unidade: str | None = Field(default=None, max_length=30)


class IndicadorUpdateSchema(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    unidade: str | None = Field(default=None, max_length=30)


class IndicadorReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_indicador: int
    nome: str
    unidade: str | None


class MedicaoIndicadorCreateSchema(BaseModel):
    id_indicador: int
    id_safra: int
    valor: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    data_referencia: date | None = None


class MedicaoIndicadorUpdateSchema(BaseModel):
    id_indicador: int | None = None
    id_safra: int | None = None
    valor: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    data_referencia: date | None = None


class MedicaoIndicadorReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_medicao: int
    id_indicador: int
    id_safra: int | None
    valor: Decimal | None
    data_referencia: date | None
    indicador_nome: str | None = None
    safra_nome: str | None = None


class ClimaSyncRequestSchema(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    id_safra: int | None = None
    data_referencia: date | None = None


class ClimaSyncResponseSchema(BaseModel):
    ids_medicao: list[int]


class CotacaoSyncRequestSchema(BaseModel):
    uf: str | None = Field(default=None, min_length=2, max_length=2)
    id_safra: int | None = None
    data_referencia: date | None = None


class CotacaoSyncResponseSchema(BaseModel):
    ids_medicao: list[int]


class IndicadorAgregacaoSchema(BaseModel):
    id_indicador: int
    indicador_nome: str | None = None
    id_safra: int | None = None
    safra_nome: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    total_medicoes: int
    valor_medio: Decimal | None = None
    valor_minimo: Decimal | None = None
    valor_maximo: Decimal | None = None
    valor_soma: Decimal | None = None


class ProdutividadeTalhaoSchema(BaseModel):
    """Produtividade (kg/ha) planejada x realizada de um talhao em uma safra."""

    id_talhao: int
    talhao_nome: str
    id_safra: int
    safra_nome: str
    safra_ano: int
    cultura_nome: str | None = None
    area_hectares: Decimal | None = None
    meta_produtividade: Decimal | None = None
    quantidade_colhida_total: Decimal | None = None
    produtividade_realizada: Decimal | None = None
    variacao_percentual: Decimal | None = None


class CustoFitossanidadeTalhaoSchema(BaseModel):
    """Custo de defensivos aplicados em um talhao em uma safra."""

    id_talhao: int
    talhao_nome: str
    id_safra: int
    safra_nome: str
    safra_ano: int
    total_aplicacoes: int
    custo_total: Decimal


class OcorrenciaFitossanidadeSchema(BaseModel):
    """Contagem de ocorrencias de agentes nocivos por severidade e talhao."""

    id_safra: int
    safra_nome: str
    safra_ano: int
    id_talhao: int
    talhao_nome: str
    nivel_severidade: str | None
    agente_nome: str | None
    total_ocorrencias: int
