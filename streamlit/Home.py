from __future__ import annotations

import streamlit as st

from app.identity import streamlit_client as auth

st.set_page_config(page_title="Agro Tech", page_icon="🌱", layout="wide")

query_params = st.query_params
if "token" in query_params:
    auth.store_token(query_params["token"])
    st.query_params.clear()
    st.rerun()

login_error = query_params.get("login_error")
if login_error:
    st.query_params.clear()
    st.error(login_error)

usuario = auth.current_user()

st.title("Agro Tech")
st.caption("Estrutura inicial")

if usuario is None:
    st.write("Faca login para acessar os modulos.")
    st.link_button("Entrar com Google", auth.get_authorization_url())
else:
    st.write(f"Bem-vindo(a), {usuario.nome}.")
    st.write(f"Perfis: {', '.join(usuario.perfis) or 'nenhum'}")
    st.write("Use o menu lateral para navegar entre os modulos.")
    if st.button("Sair"):
        auth.logout()
        st.rerun()
