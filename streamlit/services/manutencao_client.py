"""HTTP client for the maintenance Streamlit UI → FastAPI."""

from __future__ import annotations

from typing import Any

import requests
import streamlit as st

from app.core.config import settings
from services.identity_client import SESSION_KEY_TOKEN


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


def list_tipos_maquina() -> list[dict[str, Any]]:
    resposta = _request("GET", "/manutencao/tipos-maquina")
    resposta.raise_for_status()
    return resposta.json()


def create_tipo_maquina(payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request("POST", "/manutencao/tipos-maquina", json=payload)
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def get_tipo_maquina(id_tipo_maquina: int) -> dict[str, Any]:
    resposta = _request("GET", f"/manutencao/tipos-maquina/{id_tipo_maquina}")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def update_tipo_maquina(id_tipo_maquina: int, payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request(
        "PUT",
        f"/manutencao/tipos-maquina/{id_tipo_maquina}",
        json=payload,
    )
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def delete_tipo_maquina(id_tipo_maquina: int) -> None:
    resposta = _request("DELETE", f"/manutencao/tipos-maquina/{id_tipo_maquina}")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))


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


def list_manutencoes_corretivas(
    *,
    id_maquina: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    params = {
        key: value
        for key, value in {
            "id_maquina": id_maquina,
            "status": status,
        }.items()
        if value is not None
    }
    resposta = _request("GET", "/manutencao/manutencoes/corretiva", params=params)
    resposta.raise_for_status()
    return resposta.json()


def create_manutencao_corretiva(payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request("POST", "/manutencao/manutencoes/corretiva", json=payload)
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def get_manutencao(id_manutencao: int) -> dict[str, Any]:
    resposta = _request("GET", f"/manutencao/manutencoes/{id_manutencao}")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def iniciar_manutencao(id_manutencao: int) -> dict[str, Any]:
    resposta = _request("POST", f"/manutencao/manutencoes/{id_manutencao}/iniciar")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def concluir_manutencao(
    id_manutencao: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resposta = _request(
        "POST",
        f"/manutencao/manutencoes/{id_manutencao}/concluir",
        json=payload or {},
    )
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def cancelar_manutencao(id_manutencao: int) -> dict[str, Any]:
    resposta = _request("POST", f"/manutencao/manutencoes/{id_manutencao}/cancelar")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def update_manutencao_corretiva(
    id_manutencao: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    resposta = _request(
        "PATCH",
        f"/manutencao/manutencoes/{id_manutencao}/corretiva",
        json=payload,
    )
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def list_planos_manutencao(
    *,
    id_maquina: int | None = None,
) -> list[dict[str, Any]]:
    params = {
        key: value
        for key, value in {"id_maquina": id_maquina}.items()
        if value is not None
    }
    resposta = _request("GET", "/manutencao/planos-manutencao", params=params)
    resposta.raise_for_status()
    return resposta.json()


def create_plano_manutencao(payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request("POST", "/manutencao/planos-manutencao", json=payload)
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def update_plano_manutencao(
    id_plano: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    resposta = _request(
        "PUT",
        f"/manutencao/planos-manutencao/{id_plano}",
        json=payload,
    )
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def delete_plano_manutencao(id_plano: int) -> None:
    resposta = _request("DELETE", f"/manutencao/planos-manutencao/{id_plano}")
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))


def list_manutencoes_preventivas(
    *,
    id_maquina: int | None = None,
    id_plano: int | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    params = {
        key: value
        for key, value in {
            "id_maquina": id_maquina,
            "id_plano": id_plano,
            "status": status,
        }.items()
        if value is not None
    }
    resposta = _request("GET", "/manutencao/manutencoes/preventiva", params=params)
    resposta.raise_for_status()
    return resposta.json()


def create_manutencao_preventiva(payload: dict[str, Any]) -> dict[str, Any]:
    resposta = _request("POST", "/manutencao/manutencoes/preventiva", json=payload)
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()


def update_manutencao_preventiva(
    id_manutencao: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    resposta = _request(
        "PATCH",
        f"/manutencao/manutencoes/{id_manutencao}/preventiva",
        json=payload,
    )
    if not resposta.ok:
        raise RuntimeError(_extract_error(resposta))
    return resposta.json()
