from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parent
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.dashboard.home import render_dashboard
from components.shared.logo.svg import LOGO_MEANING_MARKDOWN
from components.shared.logo.widgets import apply_sidebar_logo, render_logo
from services.identity_client import (
    current_user,
    get_authorization_url,
    logout,
    store_token,
)

st.set_page_config(page_title="Agro Tech", layout="wide")

query_params = st.query_params
if "token" in query_params:
    store_token(query_params["token"])
    st.query_params.clear()
    st.rerun()

login_error = query_params.get("login_error")
if login_error:
    st.query_params.clear()
    st.error(login_error)

usuario = current_user()


def _inicio() -> None:
    apply_sidebar_logo()
    render_logo(width=420, animated=True, height=380)

    st.markdown(
        """
        <div style="text-align:center; margin-top:0.15rem;">
          <h1 style="margin-bottom:0.3rem; letter-spacing:0.04em; font-weight:600;">Agro Tech</h1>
          <p style="opacity:0.75; margin:0 auto; max-width:28rem; font-size:1.05rem;">
            Integracao que multiplica resultado.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _left, mid, _right = st.columns([4, 2, 4])
    with mid:
        with st.popover("Sobre a logo", use_container_width=True):
            st.markdown(LOGO_MEANING_MARKDOWN)

    st.divider()

    if usuario is None:
        st.write("Faca login para acessar os modulos.")
        st.link_button("Entrar com Google", get_authorization_url())
        return

    col_bemvindo, col_sair = st.columns([5, 1])
    with col_bemvindo:
        st.write(f"Bem-vindo(a), {usuario.nome}.")
        st.caption(f"Perfis: {', '.join(usuario.perfis) or 'nenhum'}")
    with col_sair:
        if st.button("Sair"):
            logout()
            st.rerun()

    st.divider()
    render_dashboard()


pages = {
    "": [st.Page(_inicio, title="Inicio", icon=":material/home:", default=True)],
    "Operacao": [
        st.Page("pages/Producao.py", title="Producao", icon=":material/agriculture:"),
        st.Page("pages/Estoque.py", title="Estoque", icon=":material/inventory_2:"),
        st.Page("pages/Manutencao.py", title="Manutencao", icon=":material/build:"),
        st.Page("pages/Logistica.py", title="Logistica", icon=":material/local_shipping:"),
        st.Page("pages/Fitossanidade.py", title="Fitossanidade", icon=":material/eco:"),
    ],
    "Comercial & Financeiro": [
        st.Page("pages/Comercial.py", title="Comercial", icon=":material/handshake:"),
        st.Page("pages/Compras.py", title="Compras", icon=":material/shopping_cart:"),
        st.Page("pages/Financeiro.py", title="Financeiro", icon=":material/payments:"),
    ],
    "Inteligencia": [
        st.Page("pages/Inteligencia.py", title="Inteligencia", icon=":material/analytics:"),
    ],
    "BI": [
        st.Page(
            "pages/bi/Estoque.py",
            title="Estoque",
            icon=":material/inventory_2:",
            url_path="bi-estoque",
        ),
        st.Page(
            "pages/bi/Compras.py",
            title="Compras",
            icon=":material/shopping_cart:",
            url_path="bi-compras",
        ),
        st.Page(
            "pages/bi/Producao.py",
            title="Produtividade",
            icon=":material/agriculture:",
            url_path="bi-producao",
        ),
        st.Page(
            "pages/bi/Fitossanidade.py",
            title="Fitossanidade",
            icon=":material/eco:",
            url_path="bi-fitossanidade",
        ),
        st.Page(
            "pages/bi/Logistica.py",
            title="Logistica",
            icon=":material/local_shipping:",
            url_path="bi-logistica",
        ),
    ],
}

pg = st.navigation(pages)
pg.run()
