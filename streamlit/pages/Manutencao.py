from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.shared.screens import setup_page
from services import manutencao_client as api
from services import producao_client as producao_api
from services.identity_client import require_login

STATUS_MAQUINA = ["DISPONIVEL", "EM_USO", "EM_MANUTENCAO", "INATIVA"]
STATUS_ORDEM = ["ABERTA", "EM_EXECUCAO", "CONCLUIDA", "CANCELADA"]


@st.cache_data(ttl=15)
def _listar_fazendas() -> list[dict]:
    return producao_api.listar("/fazendas")


@st.cache_data(ttl=15)
def _listar_tipos_maquina() -> list[dict]:
    return api.list_tipos_maquina()


def _invalidar_cache_maquinas() -> None:
    _listar_fazendas.clear()
    _listar_tipos_maquina.clear()


def _rotulo_fazenda(fazenda: dict) -> str:
    localizacao = fazenda.get("localizacao")
    if localizacao:
        return f"{fazenda['nome']} — {localizacao}"
    return fazenda["nome"]


def _selecionar_fazenda(
    label: str,
    fazendas: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
) -> int | None:
    if not fazendas and not permitir_todos:
        st.caption("Cadastre uma fazenda em Producao antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for fazenda in fazendas:
        rotulo = _rotulo_fazenda(fazenda)
        opcoes.append(rotulo)
        mapa[rotulo] = fazenda["id_fazenda"]

    escolha = st.selectbox(label, opcoes, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


def _selecionar_tipo_maquina(
    label: str,
    tipos: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    id_atual: int | None = None,
) -> int | None:
    if not tipos and not permitir_todos:
        st.caption("Cadastre um tipo de maquina antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for tipo in tipos:
        rotulo = tipo["descricao"]
        opcoes.append(rotulo)
        mapa[rotulo] = tipo["id_tipo_maquina"]

    index = 0
    if id_atual is not None:
        for indice, rotulo in enumerate(opcoes):
            if mapa.get(rotulo) == id_atual:
                index = indice
                break

    escolha = st.selectbox(label, opcoes, index=index, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


def _formatar_maquinas(maquinas: list[dict]) -> list[dict]:
    return [
        {
            "id_maquina": maquina["id_maquina"],
            "fazenda": maquina.get("nome_fazenda") or "—",
            "tipo": maquina.get("descricao_tipo") or "—",
            "nome": maquina["nome"],
            "status": maquina["status"],
        }
        for maquina in maquinas
    ]


def _render_tipos_maquina() -> None:
    st.subheader("Tipos de maquina")

    try:
        tipos = _listar_tipos_maquina()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar tipos de maquina: {exc}")
        tipos = []

    if tipos:
        st.dataframe(
            [{"tipo": tipo["descricao"]} for tipo in tipos],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum tipo cadastrado.")

    st.divider()

    col_novo, col_editar = st.columns(2)

    with col_novo:
        st.markdown("**Novo tipo**")
        with st.form("form_novo_tipo_maquina"):
            descricao = st.text_input(
                "Descricao do tipo",
                placeholder="Trator, Colheitadeira...",
            )
            criar_tipo = st.form_submit_button("Cadastrar tipo")

        if criar_tipo:
            if not descricao.strip():
                st.error("Informe a descricao do tipo.")
            else:
                try:
                    api.create_tipo_maquina({"descricao": descricao.strip()})
                    _invalidar_cache_maquinas()
                    st.success("Tipo de maquina cadastrado.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with col_editar:
        st.markdown("**Editar / excluir**")
        if not tipos:
            st.caption("Cadastre um tipo para editar.")
            return

        opcoes = {tipo["descricao"]: tipo for tipo in tipos}
        selecionado = st.selectbox(
            "Tipo",
            list(opcoes.keys()),
            key="sel_tipo_maquina",
        )
        tipo = opcoes[selecionado]

        with st.form("form_editar_tipo_maquina"):
            nova_descricao = st.text_input("Descricao", value=tipo["descricao"])
            salvar = st.form_submit_button("Salvar alteracoes")

        if salvar:
            if not nova_descricao.strip():
                st.error("Informe a descricao do tipo.")
            else:
                try:
                    api.update_tipo_maquina(
                        tipo["id_tipo_maquina"],
                        {"descricao": nova_descricao.strip()},
                    )
                    _invalidar_cache_maquinas()
                    st.success("Tipo de maquina atualizado.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if st.button("Excluir tipo", type="secondary"):
            try:
                api.delete_tipo_maquina(tipo["id_tipo_maquina"])
                _invalidar_cache_maquinas()
                st.success("Tipo de maquina excluido.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_maquinas() -> None:
    st.subheader("Maquinas")

    try:
        fazendas = _listar_fazendas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar fazendas: {exc}")
        fazendas = []

    try:
        tipos_maquina = _listar_tipos_maquina()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar tipos de maquina: {exc}")
        tipos_maquina = []

    with st.expander("Filtros", expanded=False):
        filtro_status = st.selectbox(
            "Status",
            options=["Todos"] + STATUS_MAQUINA,
            key="filtro_status_maquina",
        )
        filtro_nome = st.text_input("Nome contem", key="filtro_nome_maquina")
        filtro_fazenda = _selecionar_fazenda(
            "Fazenda",
            fazendas,
            key="filtro_fazenda_maquina",
            permitir_todos=True,
        )
        filtro_tipo = _selecionar_tipo_maquina(
            "Tipo",
            tipos_maquina,
            key="filtro_tipo_maquina",
            permitir_todos=True,
        )

    try:
        maquinas = api.list_maquinas(
            status=None if filtro_status == "Todos" else filtro_status,
            nome=filtro_nome or None,
            id_fazenda=filtro_fazenda,
            id_tipo_maquina=filtro_tipo,
        )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar maquinas: {exc}")
        maquinas = []

    if maquinas:
        st.dataframe(
            _formatar_maquinas(maquinas),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhuma maquina encontrada.")

    st.divider()

    col_nova, col_editar = st.columns(2)

    with col_nova:
        st.markdown("**Nova maquina**")
        with st.form("form_nova_maquina"):
            id_fazenda = _selecionar_fazenda(
                "Fazenda",
                fazendas,
                key="nova_maquina_fazenda",
            )
            id_tipo_maquina = _selecionar_tipo_maquina(
                "Tipo",
                tipos_maquina,
                key="nova_maquina_tipo",
            )
            nome = st.text_input("Nome")
            status = st.selectbox("Status", STATUS_MAQUINA)
            criar = st.form_submit_button("Cadastrar")

        if criar:
            if id_fazenda is None:
                st.error("Selecione uma fazenda.")
            elif id_tipo_maquina is None:
                st.error("Selecione um tipo de maquina.")
            elif not nome.strip():
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
            f"#{m['id_maquina']} - {m['nome']} ({m.get('descricao_tipo') or 'sem tipo'})": m
            for m in maquinas
        }
        selecionada = st.selectbox("Maquina", list(opcoes.keys()), key="sel_maquina")
        maquina = opcoes[selecionada]
        maquina_id = int(maquina["id_maquina"])

        with st.form(f"form_editar_maquina_{maquina_id}"):
            novo_tipo = _selecionar_tipo_maquina(
                "Tipo",
                tipos_maquina,
                key=f"editar_maquina_tipo_{maquina_id}",
                id_atual=int(maquina["id_tipo_maquina"]),
            )
            novo_nome = st.text_input(
                "Nome",
                value=maquina["nome"],
                key=f"editar_maquina_nome_{maquina_id}",
            )
            novo_status = st.selectbox(
                "Status",
                STATUS_MAQUINA,
                index=STATUS_MAQUINA.index(maquina["status"]),
                key=f"editar_maquina_status_{maquina_id}",
            )
            salvar = st.form_submit_button("Salvar alteracoes")

        if salvar:
            if novo_tipo is None:
                st.error("Selecione um tipo de maquina.")
            else:
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

tab_tipos, tab_maquinas, tab_ordens = st.tabs(
    ["Tipos de maquina", "Maquinas", "Ordens de servico"]
)

with tab_tipos:
    _render_tipos_maquina()

with tab_maquinas:
    _render_maquinas()

with tab_ordens:
    _render_ordens_servico()
