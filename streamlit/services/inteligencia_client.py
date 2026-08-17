"""HTTP client for the inteligencia Streamlit UI → FastAPI."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import requests
import streamlit as st

from app.core.config import settings
from app.inteligencia.schemas import (
    ClimaSyncRequestSchema,
    ClimaSyncResponseSchema,
    CotacaoSyncRequestSchema,
    CotacaoSyncResponseSchema,
    CustoFitossanidadeTalhaoSchema,
    IndicadorAgregacaoSchema,
    IndicadorCreateSchema,
    IndicadorReadSchema,
    IndicadorUpdateSchema,
    MedicaoIndicadorCreateSchema,
    MedicaoIndicadorReadSchema,
    MedicaoIndicadorUpdateSchema,
    OcorrenciaFitossanidadeSchema,
    ProdutividadeTalhaoSchema,
)
from app.integrations.schemas import MarketPriceData, WeatherData
from services.identity_client import SESSION_KEY_TOKEN


_API_DETAIL_TO_PT: tuple[tuple[str, str], ...] = (
    ("ja cadastrado", "Indicador com este nome ja cadastrado."),
    ("possui medicoes", "Indicador possui medicoes e nao pode ser excluido."),
    ("Ja existe medicao", "Ja existe medicao para este indicador, safra e data."),
    ("Informe o valor", "Informe o valor da medicao."),
    ("nao encontrado", "Registro nao encontrado."),
    ("nao encontrada", "Registro nao encontrado."),
    ("Data de referencia nao pode ser futura", "Data de referencia nao pode ser futura."),
    ("data_fim deve ser", "Data fim deve ser maior ou igual a data inicio."),
)


def _to_user_message(detail: str, status_code: int | None) -> str:
    lowered = detail.lower()
    for needle, portuguese in _API_DETAIL_TO_PT:
        if needle.lower() in lowered:
            return portuguese
    if status_code == 404:
        return "Registro nao encontrado."
    if status_code == 409:
        return detail or "Conflito ao processar a operacao."
    if status_code == 400:
        return detail or "Nao foi possivel concluir a operacao."
    if status_code == 422:
        return "Dados invalidos. Revise o formulario."
    return "Falha na comunicacao com a API."


class InteligenciaApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.user_message = _to_user_message(message, status_code)
        super().__init__(message)


class InteligenciaClient:
    def __init__(self, base_url: str | None = None, timeout: float = 15) -> None:
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _headers(self) -> dict[str, str]:
        token = st.session_state.get(SESSION_KEY_TOKEN)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _raise_for_api(self, response: requests.Response) -> None:
        if response.ok:
            return
        try:
            payload = response.json()
            detail = str(payload.get("detail", response.text))
        except Exception:
            detail = response.text or response.reason
        raise InteligenciaApiError(detail, status_code=response.status_code)

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        return requests.request(
            method,
            self._url(path),
            headers=self._headers(),
            timeout=self.timeout,
            **kwargs,
        )

    # --- Indicadores ---

    def list_indicadores(
        self,
        *,
        nome: str | None = None,
        unidade: str | None = None,
    ) -> list[IndicadorReadSchema]:
        params = {k: v for k, v in {"nome": nome, "unidade": unidade}.items() if v}
        response = self._request("GET", "/inteligencia/indicadores", params=params)
        self._raise_for_api(response)
        return [IndicadorReadSchema.model_validate(item) for item in response.json()]

    def create_indicador(self, payload: IndicadorCreateSchema) -> IndicadorReadSchema:
        response = self._request(
            "POST",
            "/inteligencia/indicadores",
            json=payload.model_dump(mode="json"),
        )
        self._raise_for_api(response)
        return IndicadorReadSchema.model_validate(response.json())

    def get_indicador(self, id_indicador: int) -> IndicadorReadSchema:
        response = self._request("GET", f"/inteligencia/indicadores/{id_indicador}")
        self._raise_for_api(response)
        return IndicadorReadSchema.model_validate(response.json())

    def update_indicador(
        self,
        id_indicador: int,
        payload: IndicadorUpdateSchema,
    ) -> IndicadorReadSchema:
        response = self._request(
            "PATCH",
            f"/inteligencia/indicadores/{id_indicador}",
            json=payload.model_dump(mode="json", exclude_unset=True),
        )
        self._raise_for_api(response)
        return IndicadorReadSchema.model_validate(response.json())

    def delete_indicador(self, id_indicador: int) -> None:
        response = self._request("DELETE", f"/inteligencia/indicadores/{id_indicador}")
        self._raise_for_api(response)

    def agregar_medicoes(
        self,
        id_indicador: int,
        *,
        id_safra: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> IndicadorAgregacaoSchema:
        params = {
            k: v
            for k, v in {
                "id_safra": id_safra,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
            }.items()
            if v is not None
        }
        response = self._request(
            "GET",
            f"/inteligencia/indicadores/{id_indicador}/agregacao",
            params=params,
        )
        self._raise_for_api(response)
        return IndicadorAgregacaoSchema.model_validate(response.json())

    # --- Medicoes ---

    def list_medicoes(
        self,
        *,
        id_indicador: int | None = None,
        id_safra: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> list[MedicaoIndicadorReadSchema]:
        params = {
            k: v
            for k, v in {
                "id_indicador": id_indicador,
                "id_safra": id_safra,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
            }.items()
            if v is not None
        }
        response = self._request("GET", "/inteligencia/medicoes", params=params)
        self._raise_for_api(response)
        return [MedicaoIndicadorReadSchema.model_validate(item) for item in response.json()]

    def create_medicao(
        self,
        payload: MedicaoIndicadorCreateSchema,
    ) -> MedicaoIndicadorReadSchema:
        response = self._request(
            "POST",
            "/inteligencia/medicoes",
            json=payload.model_dump(mode="json"),
        )
        self._raise_for_api(response)
        return MedicaoIndicadorReadSchema.model_validate(response.json())

    def get_medicao(self, id_medicao: int) -> MedicaoIndicadorReadSchema:
        response = self._request("GET", f"/inteligencia/medicoes/{id_medicao}")
        self._raise_for_api(response)
        return MedicaoIndicadorReadSchema.model_validate(response.json())

    def update_medicao(
        self,
        id_medicao: int,
        payload: MedicaoIndicadorUpdateSchema,
    ) -> MedicaoIndicadorReadSchema:
        response = self._request(
            "PATCH",
            f"/inteligencia/medicoes/{id_medicao}",
            json=payload.model_dump(mode="json", exclude_unset=True),
        )
        self._raise_for_api(response)
        return MedicaoIndicadorReadSchema.model_validate(response.json())

    def delete_medicao(self, id_medicao: int) -> None:
        response = self._request("DELETE", f"/inteligencia/medicoes/{id_medicao}")
        self._raise_for_api(response)

    # --- Clima (Open-Meteo) ---

    def get_clima_atual(self, *, latitude: float, longitude: float) -> WeatherData:
        response = self._request(
            "GET",
            "/inteligencia/indicadores/clima/atual",
            params={"latitude": latitude, "longitude": longitude},
        )
        self._raise_for_api(response)
        return WeatherData.model_validate(response.json())

    def sync_clima(self, payload: ClimaSyncRequestSchema) -> ClimaSyncResponseSchema:
        response = self._request(
            "POST",
            "/inteligencia/indicadores/clima/sync",
            json=payload.model_dump(mode="json"),
        )
        self._raise_for_api(response)
        return ClimaSyncResponseSchema.model_validate(response.json())

    # --- Cotacao (AgroDoc / CEPEA) ---

    def get_cotacao_atual(self, *, uf: str | None = None) -> list[MarketPriceData]:
        response = self._request(
            "GET",
            "/inteligencia/indicadores/cotacao/atual",
            params={"uf": uf} if uf else None,
        )
        self._raise_for_api(response)
        return [MarketPriceData.model_validate(item) for item in response.json()]

    def sync_cotacao(self, payload: CotacaoSyncRequestSchema) -> CotacaoSyncResponseSchema:
        response = self._request(
            "POST",
            "/inteligencia/indicadores/cotacao/sync",
            json=payload.model_dump(mode="json"),
        )
        self._raise_for_api(response)
        return CotacaoSyncResponseSchema.model_validate(response.json())

    # --- Produtividade (planejado x realizado) ---

    def listar_produtividade(
        self,
        *,
        id_safra: int | None = None,
        id_talhao: int | None = None,
    ) -> list[ProdutividadeTalhaoSchema]:
        params = {
            k: v
            for k, v in {"id_safra": id_safra, "id_talhao": id_talhao}.items()
            if v is not None
        }
        response = self._request("GET", "/inteligencia/produtividade", params=params)
        self._raise_for_api(response)
        return [ProdutividadeTalhaoSchema.model_validate(item) for item in response.json()]

    # --- Fitossanidade (custo e ocorrencias) ---

    def listar_custos_fitossanidade(
        self,
        *,
        id_safra: int | None = None,
        id_talhao: int | None = None,
    ) -> list[CustoFitossanidadeTalhaoSchema]:
        params = {
            k: v
            for k, v in {"id_safra": id_safra, "id_talhao": id_talhao}.items()
            if v is not None
        }
        response = self._request(
            "GET", "/inteligencia/fitossanidade/custos", params=params
        )
        self._raise_for_api(response)
        return [
            CustoFitossanidadeTalhaoSchema.model_validate(item) for item in response.json()
        ]

    def listar_ocorrencias_fitossanidade(
        self,
        *,
        id_safra: int | None = None,
        id_talhao: int | None = None,
    ) -> list[OcorrenciaFitossanidadeSchema]:
        params = {
            k: v
            for k, v in {"id_safra": id_safra, "id_talhao": id_talhao}.items()
            if v is not None
        }
        response = self._request(
            "GET", "/inteligencia/fitossanidade/ocorrencias", params=params
        )
        self._raise_for_api(response)
        return [
            OcorrenciaFitossanidadeSchema.model_validate(item) for item in response.json()
        ]
