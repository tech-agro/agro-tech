"""Cliente HTTP do Streamlit para a API de manutencao."""

from __future__ import annotations

from typing import Any

import requests
import streamlit as st

from app.core.config import settings
from app.identity.streamlit_client import SESSION_KEY_TOKEN


def _headers() -> dict[str, str]:
    token = st.session_state.get(SESSION_KEY_TOKEN)
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _request(method: str, path: str, **kwargs: Any) -> requests.Response:
    url = f"{settings.api_base_url}{path}"
    return requests.request(method, url, headers=_headers(), timeout=15, **kwargs)


def _extract_error(resposta: requests.Response) -> str:
    try:
        detail = resposta.json().get("detail")
    except ValueError:
        return resposta.text or "Erro desconhecido na API."
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    return str(detail)


def list_maquinas(
    *,
    id_tipo_maquina: int | None = None,
    id_fazenda: int | None = None,
    status: str | None = None,
    nome: str | None = None,
) -> list[dict[str, Any]]:
    params = {
        key: value
        for key, value in {
            "id_tipo_maquina": id_tipo_maquina,
            "id_fazenda": id_fazenda,
            "status": status,
            "nome": nome,
        }.items()
        if value is not None
    }
    resposta = _request("GET", "/manutencao/maquinas", params=params)
    resposta.raise_for_status()
    return resposta.json()


def create_maquina(payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request("POST", "/manutencao/maquinas", json=payload)
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def update_maquina(id_maquina: int, payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request("PUT", f"/manutencao/maquinas/{id_maquina}", json=payload)
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def delete_maquina(id_maquina: int) -> None:
    resposta = _request("DELETE", f"/manutencao/maquinas/{id_maquina}")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))


def list_ordens_servico(
    *,
    id_manutencao: int | None = None,
    id_maquina: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    params = {
        key: value
        for key, value in {
            "id_manutencao": id_manutencao,
            "id_maquina": id_maquina,
            "status": status,
        }.items()
        if value is not None
    }
    resposta = _request("GET", "/manutencao/ordens-servico", params=params)
    resposta.raise_for_status()
    return resposta.json()


def create_ordem_servico(payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request("POST", "/manutencao/ordens-servico", json=payload)
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def update_ordem_servico(
    id_ordem_servico: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    resposta = _request(
        "PUT",
        f"/manutencao/ordens-servico/{id_ordem_servico}",
        json=payload,
    )
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def concluir_ordem_servico(id_ordem_servico: int) -> dict[str, Any]:
    resposta = _request(
        "POST",
        f"/manutencao/ordens-servico/{id_ordem_servico}/concluir",
    )
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def delete_ordem_servico(id_ordem_servico: int) -> None:
    resposta = _request("DELETE", f"/manutencao/ordens-servico/{id_ordem_servico}")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
