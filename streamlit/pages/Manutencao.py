from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.shared.screens import setup_page
from services import manutencao_client as api
from services.identity_client import require_login

STATUS_MAQUINA = ["DISPONIVEL", "EM_USO", "EM_MANUTENCAO", "INATIVA"]
STATUS_ORDEM = ["ABERTA", "EM_EXECUCAO", "CONCLUIDA", "CANCELADA"]


def _render_maquinas() -> None:
    st.subheader("Maquinas")

    with st.expander("Filtros", expanded=False):
        filtro_status = st.selectbox(
            "Status",
            options=["Todos"] + STATUS_MAQUINA,
            key="filtro_status_maquina",
        )
        filtro_nome = st.text_input("Nome contem", key="filtro_nome_maquina")
        filtro_fazenda = st.number_input(
            "ID fazenda",
            min_value=0,
            step=1,
            value=0,
            key="filtro_fazenda_maquina",
        )
        filtro_tipo = st.number_input(
            "ID tipo maquina",
            min_value=0,
            step=1,
            value=0,
            key="filtro_tipo_maquina",
        )

    try:
        maquinas = api.list_maquinas(
            status=None if filtro_status == "Todos" else filtro_status,
            nome=filtro_nome or None,
            id_fazenda=filtro_fazenda or None,
            id_tipo_maquina=filtro_tipo or None,
        )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar maquinas: {exc}")
        maquinas = []

    if maquinas:
        st.dataframe(maquinas, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma maquina encontrada.")

    st.divider()

    col_nova, col_editar = st.columns(2)

    with col_nova:
        st.markdown("**Nova maquina**")
        with st.form("form_nova_maquina"):
            id_fazenda = st.number_input("ID fazenda", min_value=1, step=1)
            id_tipo_maquina = st.number_input("ID tipo maquina", min_value=1, step=1)
            nome = st.text_input("Nome")
            status = st.selectbox("Status", STATUS_MAQUINA)
            criar = st.form_submit_button("Cadastrar")

        if criar:
            if not nome.strip():
                st.error("Informe o nome da maquina.")
            else:
                try:
                    api.create_maquina(
                        {
                            "id_fazenda": int(id_fazenda),
                            "id_tipo_maquina": int(id_tipo_maquina),
                            "nome": nome.strip(),
                            "status": status,
                        }
                    )
                    st.success("Maquina cadastrada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with col_editar:
        st.markdown("**Editar / excluir**")
        if not maquinas:
            st.caption("Cadastre uma maquina para editar.")
            return

        opcoes = {
            f"#{m['id_maquina']} - {m['nome']} ({m['status']})": m for m in maquinas
        }
        selecionada = st.selectbox("Maquina", list(opcoes.keys()), key="sel_maquina")
        maquina = opcoes[selecionada]

        with st.form("form_editar_maquina"):
            novo_tipo = st.number_input(
                "ID tipo maquina",
                min_value=1,
                step=1,
                value=int(maquina["id_tipo_maquina"]),
            )
            novo_nome = st.text_input("Nome", value=maquina["nome"])
            novo_status = st.selectbox(
                "Status",
                STATUS_MAQUINA,
                index=STATUS_MAQUINA.index(maquina["status"]),
            )
            salvar = st.form_submit_button("Salvar alteracoes")

        if salvar:
            try:
                api.update_maquina(
                    maquina["id_maquina"],
                    {
                        "id_tipo_maquina": int(novo_tipo),
                        "nome": novo_nome.strip(),
                        "status": novo_status,
                    },
                )
                st.success("Maquina atualizada.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if st.button("Excluir maquina", type="secondary"):
            try:
                api.delete_maquina(maquina["id_maquina"])
                st.success("Maquina excluida.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_ordens_servico() -> None:
    st.subheader("Ordens de servico")

    with st.expander("Filtros", expanded=False):
        filtro_status = st.selectbox(
            "Status",
            options=["Todos"] + STATUS_ORDEM,
            key="filtro_status_os",
        )
        filtro_manutencao = st.number_input(
            "ID manutencao",
            min_value=0,
            step=1,
            value=0,
            key="filtro_manutencao_os",
        )
        filtro_maquina = st.number_input(
            "ID maquina",
            min_value=0,
            step=1,
            value=0,
            key="filtro_maquina_os",
        )

    try:
        ordens = api.list_ordens_servico(
            status=None if filtro_status == "Todos" else filtro_status,
            id_manutencao=filtro_manutencao or None,
            id_maquina=filtro_maquina or None,
        )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar ordens de servico: {exc}")
        ordens = []

    if ordens:
        st.dataframe(ordens, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma ordem de servico encontrada.")

    st.divider()

    col_nova, col_editar = st.columns(2)

    with col_nova:
        st.markdown("**Nova ordem de servico**")
        with st.form("form_nova_os"):
            id_manutencao = st.number_input("ID manutencao", min_value=1, step=1)
            descricao = st.text_area("Descricao")
            status = st.selectbox("Status inicial", STATUS_ORDEM[:2])
            criar = st.form_submit_button("Abrir OS")

        if criar:
            try:
                api.create_ordem_servico(
                    {
                        "id_manutencao": int(id_manutencao),
                        "descricao": descricao.strip() or None,
                        "status": status,
                    }
                )
                st.success("Ordem de servico criada.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with col_editar:
        st.markdown("**Gerenciar OS**")
        if not ordens:
            st.caption("Cadastre uma ordem de servico para gerenciar.")
            return

        opcoes = {
            f"#{o['id_ordem_servico']} - manut. {o['id_manutencao']} ({o['status']})": o
            for o in ordens
        }
        selecionada = st.selectbox("Ordem de servico", list(opcoes.keys()), key="sel_os")
        ordem = opcoes[selecionada]

        with st.form("form_editar_os"):
            nova_descricao = st.text_area(
                "Descricao",
                value=ordem.get("descricao") or "",
            )
            novo_status = st.selectbox(
                "Status",
                STATUS_ORDEM,
                index=STATUS_ORDEM.index(ordem["status"]),
            )
            salvar = st.form_submit_button("Salvar alteracoes")

        if salvar:
            try:
                api.update_ordem_servico(
                    ordem["id_ordem_servico"],
                    {
                        "descricao": nova_descricao.strip() or None,
                        "status": novo_status,
                    },
                )
                st.success("Ordem de servico atualizada.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if ordem["status"] == "EM_EXECUCAO":
            if st.button("Concluir OS", type="primary"):
                try:
                    api.concluir_ordem_servico(ordem["id_ordem_servico"])
                    st.success("Ordem de servico concluida.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if ordem["status"] != "CONCLUIDA":
            if st.button("Excluir OS", type="secondary"):
                try:
                    api.delete_ordem_servico(ordem["id_ordem_servico"])
                    st.success("Ordem de servico excluida.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


require_login()

setup_page("Manutencao", "Gestao de maquinas e ordens de servico.")

tab_maquinas, tab_ordens = st.tabs(["Maquinas", "Ordens de servico"])

with tab_maquinas:
    _render_maquinas()

with tab_ordens:
    _render_ordens_servico()
