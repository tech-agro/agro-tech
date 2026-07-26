"""Schemas Pydantic da entidade certificacao_lote."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enum import StatusCertificacao


class CertificacaoLoteCreateSchema(BaseModel):
    id_certificacao: int
    id_lote: int
    dt_emissao: date | None = None
    dt_validade: date | None = None
    numero_certificado: str | None = Field(default=None, min_length=1, max_length=120)
    status: StatusCertificacao

    @model_validator(mode="after")
    def validar_periodo(self) -> "CertificacaoLoteCreateSchema":
        if self.dt_emissao and self.dt_validade and self.dt_validade < self.dt_emissao:
            raise ValueError("dt_validade não pode ser anterior a dt_emissao")
        return self


class CertificacaoLoteUpdateSchema(BaseModel):
    dt_emissao: date | None = None
    dt_validade: date | None = None
    numero_certificado: str | None = Field(default=None, min_length=1, max_length=120)
    status: StatusCertificacao | None = None

    @model_validator(mode="after")
    def validar_periodo(self) -> "CertificacaoLoteUpdateSchema":
        if self.dt_emissao and self.dt_validade and self.dt_validade < self.dt_emissao:
            raise ValueError("dt_validade não pode ser anterior a dt_emissao")
        return self


class CertificacaoLoteReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cert_lote: int
    id_certificacao: int
    id_lote: int
    dt_emissao: date | None
    dt_validade: date | None
    numero_certificado: str | None
    status: StatusCertificacao
    lote_codigo: str | None = None
    certificacao_nome: str | None = None