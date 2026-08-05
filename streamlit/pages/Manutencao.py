from __future__ import annotations

from datetime import date
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
STATUS_MANUTENCAO = ["ABERTA", "EM_EXECUCAO", "CONCLUIDA", "CANCELADA"]


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


def _selecionar_maquina(
    label: str,
    maquinas: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    id_atual: int | None = None,
) -> int | None:
    if not maquinas and not permitir_todos:
        st.caption("Cadastre uma maquina antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for maquina in maquinas:
        rotulo = f"#{maquina['id_maquina']} - {maquina['nome']}"
        opcoes.append(rotulo)
        mapa[rotulo] = maquina["id_maquina"]

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


def _rotulo_manutencao(item: dict) -> str:
    manutencao = item["manutencao"]
    nome = item.get("nome_maquina") or "maquina"
    defeito = item["corretiva"].get("defeito_relatado") or "sem defeito"
    data = manutencao.get("dt_inicio") or "—"
    return (
        f"#{manutencao['id_manutencao']} - {nome} "
        f"({manutencao['status']}) - {defeito} [{data}]"
    )


def _selecionar_manutencao(
    label: str,
    manutencoes: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    apenas_abertas: bool = False,
) -> int | None:
    itens = manutencoes
    if apenas_abertas:
        itens = [
            item
            for item in manutencoes
            if item["manutencao"]["status"] in {"ABERTA", "EM_EXECUCAO"}
        ]

    if not itens and not permitir_todos:
        st.caption("Registre uma manutencao corretiva aberta antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for item in itens:
        rotulo = _rotulo_manutencao(item)
        opcoes.append(rotulo)
        mapa[rotulo] = item["manutencao"]["id_manutencao"]

    escolha = st.selectbox(label, opcoes, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


PERIODICIDADE_OPCOES = [
    "30 DIAS",
    "60 DIAS",
    "90 DIAS",
    "180 DIAS",
    "6 MESES",
    "12 MESES",
    "500 HORAS",
    "1000 HORAS",
]


def _plano_usa_hodometro(plano: dict) -> bool:
    return "HORA" in (plano.get("periodicidade") or "").upper()


def _rotulo_plano(plano: dict) -> str:
    nome = plano.get("nome_maquina") or "maquina"
    periodicidade = plano.get("periodicidade") or "—"
    proxima = plano.get("proxima_execucao") or "—"
    return f"#{plano['id_plano']} - {nome} ({periodicidade}) prox: {proxima}"


def _selecionar_plano(
    label: str,
    planos: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    id_maquina: int | None = None,
) -> dict | None:
    itens = planos
    if id_maquina is not None:
        itens = [plano for plano in planos if plano["id_maquina"] == id_maquina]

    if not itens and not permitir_todos:
        st.caption("Cadastre um plano de manutencao antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, dict] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for plano in itens:
        rotulo = _rotulo_plano(plano)
        opcoes.append(rotulo)
        mapa[rotulo] = plano

    escolha = st.selectbox(label, opcoes, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


def _formatar_planos(planos: list[dict]) -> list[dict]:
    return [
        {
            "id": plano["id_plano"],
            "maquina": plano.get("nome_maquina") or "—",
            "periodicidade": plano.get("periodicidade") or "—",
            "proxima_execucao": plano.get("proxima_execucao") or "—",
        }
        for plano in planos
    ]


def _formatar_preventivas(itens: list[dict]) -> list[dict]:
    return [
        {
            "id": item["manutencao"]["id_manutencao"],
            "plano": item["preventiva"]["id_plano"],
            "maquina": item.get("nome_maquina") or "—",
            "periodicidade": item.get("periodicidade") or "—",
            "status": item["manutencao"]["status"],
            "data_execucao": item["manutencao"].get("dt_inicio") or "—",
            "hodometro": item["preventiva"].get("hodometro_execucao"),
            "proxima_execucao": item.get("proxima_execucao_plano") or "—",
            "custo": item["manutencao"].get("custo"),
            "dt_fim": item["manutencao"].get("dt_fim"),
        }
        for item in itens
    ]


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


def _render_planos_manutencao() -> None:
    st.subheader("Planos de manutencao")

    try:
        maquinas = api.list_maquinas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar maquinas: {exc}")
        maquinas = []

    with st.expander("Filtros", expanded=False):
        filtro_maquina = _selecionar_maquina(
            "Maquina",
            maquinas,
            key="filtro_maquina_plano",
            permitir_todos=True,
        )

    try:
        planos = api.list_planos_manutencao(id_maquina=filtro_maquina)
    except Exception as exc:
        st.error(f"Nao foi possivel carregar planos: {exc}")
        planos = []

    if planos:
        st.dataframe(
            _formatar_planos(planos),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum plano de manutencao encontrado.")

    st.divider()

    col_novo, col_editar = st.columns(2)

    with col_novo:
        st.markdown("**Novo plano**")
        with st.form("form_novo_plano"):
            id_maquina = _selecionar_maquina(
                "Maquina",
                maquinas,
                key="novo_plano_maquina",
            )
            periodicidade = st.selectbox("Periodicidade", PERIODICIDADE_OPCOES)
            proxima_execucao = st.date_input(
                "Proxima execucao",
                value=date.today(),
            )
            criar = st.form_submit_button("Cadastrar plano")

        if criar:
            if id_maquina is None:
                st.error("Selecione uma maquina.")
            else:
                try:
                    api.create_plano_manutencao(
                        {
                            "id_maquina": int(id_maquina),
                            "periodicidade": periodicidade,
                            "proxima_execucao": proxima_execucao.isoformat(),
                        }
                    )
                    st.success("Plano cadastrado.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with col_editar:
        st.markdown("**Editar / excluir**")
        if not planos:
            st.caption("Cadastre um plano para editar.")
            return

        opcoes = {_rotulo_plano(plano): plano for plano in planos}
        selecionado = st.selectbox("Plano", list(opcoes.keys()), key="sel_plano")
        plano = opcoes[selecionado]
        plano_id = int(plano["id_plano"])

        with st.form(f"form_editar_plano_{plano_id}"):
            nova_periodicidade = st.selectbox(
                "Periodicidade",
                PERIODICIDADE_OPCOES,
                index=(
                    PERIODICIDADE_OPCOES.index(plano["periodicidade"])
                    if plano.get("periodicidade") in PERIODICIDADE_OPCOES
                    else 0
                ),
            )
            proxima_atual = plano.get("proxima_execucao")
            if isinstance(proxima_atual, str):
                proxima_atual = date.fromisoformat(proxima_atual)
            nova_proxima = st.date_input(
                "Proxima execucao",
                value=proxima_atual or date.today(),
            )
            salvar = st.form_submit_button("Salvar alteracoes")

        if salvar:
            try:
                api.update_plano_manutencao(
                    plano_id,
                    {
                        "periodicidade": nova_periodicidade,
                        "proxima_execucao": nova_proxima.isoformat(),
                    },
                )
                st.success("Plano atualizado.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if st.button("Excluir plano", type="secondary", key=f"excluir_plano_{plano_id}"):
            try:
                api.delete_plano_manutencao(plano_id)
                st.success("Plano excluido.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_manutencao_preventiva() -> None:
    st.subheader("Manutencao preventiva")

    try:
        maquinas = api.list_maquinas()
        planos = api.list_planos_manutencao()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar dados: {exc}")
        maquinas = []
        planos = []

    with st.expander("Filtros", expanded=False):
        filtro_status = st.selectbox(
            "Status",
            options=["Todos"] + STATUS_MANUTENCAO,
            key="filtro_status_preventiva",
        )
        filtro_maquina = _selecionar_maquina(
            "Maquina",
            maquinas,
            key="filtro_maquina_preventiva",
            permitir_todos=True,
        )
        filtro_plano = _selecionar_plano(
            "Plano",
            planos,
            key="filtro_plano_preventiva",
            permitir_todos=True,
            id_maquina=filtro_maquina,
        )

    try:
        preventivas = api.list_manutencoes_preventivas(
            status=None if filtro_status == "Todos" else filtro_status,
            id_maquina=filtro_maquina,
            id_plano=int(filtro_plano["id_plano"]) if filtro_plano else None,
        )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar manutencoes preventivas: {exc}")
        preventivas = []

    if preventivas:
        st.dataframe(
            _formatar_preventivas(preventivas),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhuma manutencao preventiva encontrada.")

    st.divider()

    col_nova, col_gerenciar = st.columns(2)

    with col_nova:
        st.markdown("**Agendar execucao**")
        if not planos:
            st.caption("Cadastre um plano de manutencao antes de continuar.")
        else:
            with st.form("form_nova_preventiva"):
                plano_selecionado = _selecionar_plano(
                    "Plano",
                    planos,
                    key="nova_preventiva_plano",
                )
                data_execucao = st.date_input("Data de execucao", value=date.today())
                hodometro_execucao = None
                if plano_selecionado and _plano_usa_hodometro(plano_selecionado):
                    hodometro_execucao = st.number_input(
                        "Hodometro atual",
                        min_value=0.0,
                        step=0.1,
                        format="%.1f",
                    )
                criar = st.form_submit_button("Abrir manutencao preventiva")

            if criar:
                if plano_selecionado is None:
                    st.error("Selecione um plano.")
                else:
                    payload = {
                        "id_maquina": int(plano_selecionado["id_maquina"]),
                        "id_plano": int(plano_selecionado["id_plano"]),
                        "status": "ABERTA",
                        "dt_inicio": data_execucao.isoformat(),
                    }
                    if hodometro_execucao is not None and hodometro_execucao > 0:
                        payload["hodometro_execucao"] = float(hodometro_execucao)
                    try:
                        api.create_manutencao_preventiva(payload)
                        st.success("Manutencao preventiva registrada.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    with col_gerenciar:
        st.markdown("**Gerenciar manutencao**")
        if not preventivas:
            st.caption("Registre uma manutencao preventiva para gerenciar.")
            return

        opcoes = {
            (
                f"#{item['manutencao']['id_manutencao']} - "
                f"{item.get('nome_maquina') or 'maquina'} "
                f"({item['manutencao']['status']})"
            ): item
            for item in preventivas
        }
        selecionada = st.selectbox(
            "Manutencao",
            list(opcoes.keys()),
            key="sel_preventiva",
        )
        item = opcoes[selecionada]
        manutencao = item["manutencao"]
        detalhe = item["preventiva"]
        manutencao_id = int(manutencao["id_manutencao"])
        status = manutencao["status"]

        st.caption(
            f"Plano #{detalhe['id_plano']} | "
            f"{item.get('periodicidade') or '—'} | "
            f"Proxima execucao do plano: {item.get('proxima_execucao_plano') or '—'}"
        )

        with st.form(f"form_editar_preventiva_{manutencao_id}"):
            dt_inicio_atual = manutencao.get("dt_inicio")
            if isinstance(dt_inicio_atual, str):
                dt_inicio_atual = date.fromisoformat(dt_inicio_atual)
            nova_data_execucao = st.date_input(
                "Data de execucao",
                value=dt_inicio_atual or date.today(),
            )
            novo_hodometro = st.number_input(
                "Hodometro de execucao",
                min_value=0.0,
                step=0.1,
                format="%.1f",
                value=float(detalhe.get("hodometro_execucao") or 0.0),
            )
            salvar = st.form_submit_button("Salvar detalhes")

        if salvar:
            try:
                payload = {
                    "dt_inicio": nova_data_execucao.isoformat(),
                }
                if novo_hodometro > 0:
                    payload["hodometro_execucao"] = float(novo_hodometro)
                api.update_manutencao_preventiva(manutencao_id, payload)
                st.success("Detalhes atualizados.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if status == "ABERTA":
            if st.button("Iniciar manutencao", type="primary", key=f"iniciar_prev_{manutencao_id}"):
                try:
                    api.iniciar_manutencao(manutencao_id)
                    st.success("Manutencao iniciada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if status in {"ABERTA", "EM_EXECUCAO"}:
            custo = st.number_input(
                "Custo (opcional)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key=f"custo_preventiva_{manutencao_id}",
            )
            if st.button("Concluir manutencao", key=f"concluir_prev_{manutencao_id}"):
                try:
                    payload = {"custo": float(custo)} if custo > 0 else {}
                    api.concluir_manutencao(manutencao_id, payload or None)
                    st.success("Manutencao concluida.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if status not in {"CONCLUIDA", "CANCELADA"}:
            if st.button("Cancelar manutencao", type="secondary", key=f"cancelar_prev_{manutencao_id}"):
                try:
                    api.cancelar_manutencao(manutencao_id)
                    st.success("Manutencao cancelada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _formatar_manutencoes_corretivas(itens: list[dict]) -> list[dict]:
    return [
        {
            "id": item["manutencao"]["id_manutencao"],
            "maquina": item.get("nome_maquina") or "—",
            "status": item["manutencao"]["status"],
            "defeito": item["corretiva"].get("defeito_relatado") or "—",
            "causa_raiz": item["corretiva"].get("causa_raiz") or "—",
            "solucao": item["corretiva"].get("solucao_aplicada") or "—",
            "data_defeito": item["manutencao"].get("dt_inicio") or "—",
            "custo": item["manutencao"].get("custo"),
            "dt_fim": item["manutencao"].get("dt_fim"),
        }
        for item in itens
    ]


def _render_manutencao_corretiva() -> None:
    st.subheader("Manutencao corretiva")

    try:
        maquinas = api.list_maquinas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar maquinas: {exc}")
        maquinas = []

    with st.expander("Filtros", expanded=False):
        filtro_status = st.selectbox(
            "Status",
            options=["Todos"] + STATUS_MANUTENCAO,
            key="filtro_status_corretiva",
        )
        filtro_maquina = _selecionar_maquina(
            "Maquina",
            maquinas,
            key="filtro_maquina_corretiva",
            permitir_todos=True,
        )

    try:
        corretivas = api.list_manutencoes_corretivas(
            status=None if filtro_status == "Todos" else filtro_status,
            id_maquina=filtro_maquina,
        )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar manutencoes corretivas: {exc}")
        corretivas = []

    if corretivas:
        st.dataframe(
            _formatar_manutencoes_corretivas(corretivas),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhuma manutencao corretiva encontrada.")

    st.divider()

    col_nova, col_gerenciar = st.columns(2)

    with col_nova:
        st.markdown("**Registrar defeito**")
        with st.form("form_nova_corretiva"):
            id_maquina = _selecionar_maquina(
                "Maquina",
                maquinas,
                key="nova_corretiva_maquina",
            )
            data_defeito = st.date_input("Data do defeito", value=date.today())
            defeito_relatado = st.text_area("Defeito relatado")
            causa_raiz = st.text_input("Causa raiz (opcional)")
            criar = st.form_submit_button("Abrir manutencao corretiva")

        if criar:
            if id_maquina is None:
                st.error("Selecione uma maquina.")
            elif not defeito_relatado.strip():
                st.error("Informe o defeito relatado.")
            else:
                try:
                    api.create_manutencao_corretiva(
                        {
                            "id_maquina": int(id_maquina),
                            "status": "ABERTA",
                            "dt_inicio": data_defeito.isoformat(),
                            "defeito_relatado": defeito_relatado.strip(),
                            "causa_raiz": causa_raiz.strip() or None,
                        }
                    )
                    st.success("Manutencao corretiva registrada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with col_gerenciar:
        st.markdown("**Gerenciar manutencao**")
        if not corretivas:
            st.caption("Registre uma manutencao corretiva para gerenciar.")
            return

        opcoes = {
            (
                f"#{item['manutencao']['id_manutencao']} - "
                f"{item.get('nome_maquina') or 'maquina'} "
                f"({item['manutencao']['status']})"
            ): item
            for item in corretivas
        }
        selecionada = st.selectbox(
            "Manutencao",
            list(opcoes.keys()),
            key="sel_corretiva",
        )
        item = opcoes[selecionada]
        manutencao = item["manutencao"]
        detalhe = item["corretiva"]
        manutencao_id = int(manutencao["id_manutencao"])
        status = manutencao["status"]

        with st.form(f"form_editar_corretiva_{manutencao_id}"):
            dt_inicio_atual = manutencao.get("dt_inicio")
            if isinstance(dt_inicio_atual, str):
                dt_inicio_atual = date.fromisoformat(dt_inicio_atual)
            nova_data_defeito = st.date_input(
                "Data do defeito",
                value=dt_inicio_atual or date.today(),
            )
            novo_defeito = st.text_area(
                "Defeito relatado",
                value=detalhe.get("defeito_relatado") or "",
            )
            nova_causa = st.text_input(
                "Causa raiz",
                value=detalhe.get("causa_raiz") or "",
            )
            nova_solucao = st.text_area(
                "Solucao aplicada",
                value=detalhe.get("solucao_aplicada") or "",
            )
            salvar = st.form_submit_button("Salvar detalhes")

        if salvar:
            try:
                api.update_manutencao_corretiva(
                    manutencao_id,
                    {
                        "dt_inicio": nova_data_defeito.isoformat(),
                        "defeito_relatado": novo_defeito.strip() or None,
                        "causa_raiz": nova_causa.strip() or None,
                        "solucao_aplicada": nova_solucao.strip() or None,
                    },
                )
                st.success("Detalhes atualizados.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if status == "ABERTA":
            if st.button("Iniciar manutencao", type="primary", key=f"iniciar_{manutencao_id}"):
                try:
                    api.iniciar_manutencao(manutencao_id)
                    st.success("Manutencao iniciada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if status in {"ABERTA", "EM_EXECUCAO"}:
            custo = st.number_input(
                "Custo (opcional)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key=f"custo_corretiva_{manutencao_id}",
            )
            if st.button("Concluir manutencao", key=f"concluir_{manutencao_id}"):
                try:
                    payload = {"custo": float(custo)} if custo > 0 else {}
                    api.concluir_manutencao(manutencao_id, payload or None)
                    st.success("Manutencao concluida.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if status not in {"CONCLUIDA", "CANCELADA"}:
            if st.button("Cancelar manutencao", type="secondary", key=f"cancelar_{manutencao_id}"):
                try:
                    api.cancelar_manutencao(manutencao_id)
                    st.success("Manutencao cancelada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _formatar_ordens_servico(ordens: list[dict]) -> list[dict]:
    return [
        {
            "id": ordem["id_ordem_servico"],
            "manutencao": ordem["id_manutencao"],
            "maquina": ordem.get("nome_maquina") or "—",
            "tipo": ordem.get("tipo_manutencao") or "—",
            "status_manutencao": ordem.get("status_manutencao") or "—",
            "defeito": ordem.get("defeito_relatado") or "—",
            "descricao": ordem.get("descricao") or "—",
            "status": ordem["status"],
        }
        for ordem in ordens
    ]


def _render_ordens_servico() -> None:
    st.subheader("Ordens de servico")

    try:
        maquinas = api.list_maquinas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar maquinas: {exc}")
        maquinas = []

    try:
        manutencoes = api.list_manutencoes_corretivas()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar manutencoes: {exc}")
        manutencoes = []

    with st.expander("Filtros", expanded=False):
        filtro_status = st.selectbox(
            "Status da OS",
            options=["Todos"] + STATUS_ORDEM,
            key="filtro_status_os",
        )
        filtro_maquina = _selecionar_maquina(
            "Maquina",
            maquinas,
            key="filtro_maquina_os",
            permitir_todos=True,
        )
        filtro_manutencao = _selecionar_manutencao(
            "Manutencao",
            manutencoes,
            key="filtro_manutencao_os",
            permitir_todos=True,
        )

    try:
        ordens = api.list_ordens_servico(
            status=None if filtro_status == "Todos" else filtro_status,
            id_manutencao=filtro_manutencao,
            id_maquina=filtro_maquina,
        )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar ordens de servico: {exc}")
        ordens = []

    if ordens:
        st.dataframe(
            _formatar_ordens_servico(ordens),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhuma ordem de servico encontrada.")

    st.divider()

    col_nova, col_editar = st.columns(2)

    with col_nova:
        st.markdown("**Nova ordem de servico**")
        manutencoes_abertas = [
            item
            for item in manutencoes
            if item["manutencao"]["status"] in {"ABERTA", "EM_EXECUCAO"}
        ]
        if not manutencoes_abertas:
            st.caption("Abra uma manutencao corretiva antes de criar uma OS.")
        else:
            with st.form("form_nova_os"):
                id_manutencao = _selecionar_manutencao(
                    "Manutencao",
                    manutencoes,
                    key="nova_os_manutencao",
                    apenas_abertas=True,
                )
                descricao = st.text_area("Descricao")
                criar = st.form_submit_button("Abrir OS")

            if criar:
                if id_manutencao is None:
                    st.error("Selecione uma manutencao.")
                else:
                    try:
                        api.create_ordem_servico(
                            {
                                "id_manutencao": int(id_manutencao),
                                "descricao": descricao.strip() or None,
                                "status": "ABERTA",
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
            (
                f"#{o['id_ordem_servico']} - {o.get('nome_maquina') or 'maquina'} "
                f"(manut. {o['id_manutencao']}, {o['status']})"
            ): o
            for o in ordens
        }
        selecionada = st.selectbox("Ordem de servico", list(opcoes.keys()), key="sel_os")
        ordem = opcoes[selecionada]
        ordem_id = int(ordem["id_ordem_servico"])

        st.caption(
            f"Manutencao #{ordem['id_manutencao']} | "
            f"{ordem.get('nome_maquina') or '—'} | "
            f"Status manutencao: {ordem.get('status_manutencao') or '—'}"
        )
        if ordem.get("defeito_relatado"):
            st.caption(f"Defeito: {ordem['defeito_relatado']}")

        with st.form(f"form_editar_os_{ordem_id}"):
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
                    ordem_id,
                    {
                        "descricao": nova_descricao.strip() or None,
                        "status": novo_status,
                    },
                )
                st.success("Ordem de servico atualizada.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if ordem["status"] == "ABERTA":
            if st.button("Iniciar OS", type="primary", key=f"iniciar_os_{ordem_id}"):
                try:
                    api.update_ordem_servico(
                        ordem_id,
                        {"status": "EM_EXECUCAO"},
                    )
                    st.success("Ordem de servico em execucao.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if ordem["status"] == "EM_EXECUCAO":
            if st.button("Concluir OS", type="primary", key=f"concluir_os_{ordem_id}"):
                try:
                    api.concluir_ordem_servico(ordem_id)
                    st.success("Ordem de servico concluida.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if ordem["status"] != "CONCLUIDA":
            if st.button("Excluir OS", type="secondary", key=f"excluir_os_{ordem_id}"):
                try:
                    api.delete_ordem_servico(ordem_id)
                    st.success("Ordem de servico excluida.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


require_login()

setup_page("Manutencao", "Gestao de maquinas, planos e manutencoes.")

tab_tipos, tab_maquinas, tab_planos, tab_preventiva, tab_corretiva, tab_ordens = st.tabs(
    [
        "Tipos de maquina",
        "Maquinas",
        "Planos de manutencao",
        "Manutencao preventiva",
        "Manutencao corretiva",
        "Ordens de servico",
    ]
)

with tab_tipos:
    _render_tipos_maquina()

with tab_maquinas:
    _render_maquinas()

with tab_planos:
    _render_planos_manutencao()

with tab_preventiva:
    _render_manutencao_preventiva()

with tab_corretiva:
    _render_manutencao_corretiva()

with tab_ordens:
    _render_ordens_servico()
