from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parent
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.shared.logo.widgets import apply_sidebar_logo, render_logo
from services.identity_client import (
    current_user,
    get_authorization_url,
    logout,
    store_token,
)

st.set_page_config(page_title="Agro Tech", layout="wide")
apply_sidebar_logo()

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

render_logo(width=320, animated=True, height=280)

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

st.divider()

if usuario is None:
    st.write("Faca login para acessar os modulos.")
    st.link_button("Entrar com Google", get_authorization_url())
else:
    st.write(f"Bem-vindo(a), {usuario.nome}.")
    st.write(f"Perfis: {', '.join(usuario.perfis) or 'nenhum'}")
    st.caption("Use o menu lateral para navegar entre os modulos.")
    if st.button("Sair"):
        logout()
        st.rerun()
