"""HTTP client for the identity Streamlit UI → FastAPI."""

from __future__ import annotations

import os

import requests
import streamlit as st

from app.core.config import settings
from app.identity.models import Usuario

SESSION_KEY_TOKEN = "auth_token"

# Set AUTH_DISABLED=true only for local bypass of Streamlit login gates.
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "true").lower() in {"1", "true", "yes"}


def get_authorization_url() -> str:
    resposta = requests.get(f"{settings.api_base_url}/auth/login", timeout=10)
    resposta.raise_for_status()
    return resposta.json()["authorization_url"]


def store_token(token: str) -> None:
    st.session_state[SESSION_KEY_TOKEN] = token


def logout() -> None:
    st.session_state.pop(SESSION_KEY_TOKEN, None)


def current_user() -> Usuario | None:
    token = st.session_state.get(SESSION_KEY_TOKEN)
    if not token:
        return None
    resposta = requests.get(
        f"{settings.api_base_url}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resposta.status_code != 200:
        st.session_state.pop(SESSION_KEY_TOKEN, None)
        return None
    return Usuario(**resposta.json())


def require_login() -> Usuario | None:
    if AUTH_DISABLED:
        return current_user()
    usuario = current_user()
    if usuario is None:
        st.warning("Faca login para acessar esta pagina.")
        st.stop()
    return usuario


def require_permission(descricao_permissao: str) -> Usuario | None:
    if AUTH_DISABLED:
        return current_user()
    usuario = require_login()
    token = st.session_state[SESSION_KEY_TOKEN]
    resposta = requests.get(
        f"{settings.api_base_url}/auth/permissions/{descricao_permissao}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resposta.status_code != 200 or not resposta.json().get("has_permission"):
        st.error("Voce nao tem permissao para acessar esta pagina.")
        st.stop()
    return usuario
