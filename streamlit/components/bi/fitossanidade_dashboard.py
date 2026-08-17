"""BI dashboard for phytosanitary cost and occurrences, by talhao/safra.

Alem do custo e das ocorrencias por talhao/safra, cruza a pressao
fitossanitaria com a produtividade (modulo Producao) para dar uma visao
global de manejo e custo.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.bi import charts
from components.bi.widgets import download_csv, fmt_brl, fmt_int
from components.shared.screens import setup_page, toast_error
from services import producao_client as producao_api
from services.inteligencia_client import InteligenciaApiError, InteligenciaClient

_TEAL = "#0E8C7D"
_AMBER = "#C9861E"
_SEVERITY_ORDER = ["Baixo", "Medio", "Alto", "Critico"]
_SEVERITY_COLORS = {
    "Baixo": "#2E7D46",
    "Medio": "#C9861E",
    "Alto": "#C1521F",
    "Critico": "#B3392B",
}
_PRESSAO_ALTA = {"Alto", "Critico"}
_PREFIX = "bi_fitossanidade"


def _client() -> InteligenciaClient:
    return InteligenciaClient()


def _safra_label(item: dict) -> str:
    return f"#{item['id_safra']} - {item['nome']} ({item.get('ano', '')})"


def _talhao_label(item: dict) -> str:
    return f"#{item['id_talhao']} - {item['nome']}"


def _load_safras() -> list[dict]:
    try:
        return producao_api.listar("/safras")
    except Exception:
        st.warning("Nao foi possivel carregar as safras para o filtro.")
        return []


def _load_talhoes(id_safra: int | None) -> list[dict]:
    try:
        return producao_api.listar("/talhoes", {"id_safra": id_safra} if id_safra else None)
    except Exception:
        return []


def _render_filtros() -> tuple[int | None, int | None]:
    safras = _load_safras()
    mapa_safra = {"Todas": None}
    mapa_safra.update({_safra_label(s): s["id_safra"] for s in safras})

    col_safra, col_talhao, col_limpar = st.columns([3, 3, 1])
    with col_safra:
        safra_escolha = st.selectbox(
            "Safra", list(mapa_safra.keys()), key=f"{_PREFIX}_safra"
        )
    id_safra = mapa_safra[safra_escolha]

    talhoes = _load_talhoes(id_safra)
    mapa_talhao = {"Todos": None}
    mapa_talhao.update({_talhao_label(t): t["id_talhao"] for t in talhoes})
    with col_talhao:
        talhao_escolha = st.selectbox(
            "Talhao", list(mapa_talhao.keys()), key=f"{_PREFIX}_talhao"
        )
    id_talhao = mapa_talhao[talhao_escolha]

    with col_limpar:
        st.caption(" ")
        if st.button(
            "Limpar",
            use_container_width=True,
            icon=":material/filter_alt_off:",
            key=f"{_PREFIX}_limpar",
            help="Volta os filtros para Todas/Todos.",
        ):
            st.session_state.pop(f"{_PREFIX}_safra", None)
            st.session_state.pop(f"{_PREFIX}_talhao", None)
            st.rerun()

    return id_safra, id_talhao


def _render_visao_geral(todos_custos: list, todos_ocorrencias: list) -> None:
    st.caption(
        "Evolucao do custo de defensivos e das ocorrencias por severidade "
        "ao longo das safras (independente do filtro abaixo)."
    )
    por_safra_custo: dict[int, dict] = {}
    for c in todos_custos:
        info = por_safra_custo.setdefault(c.id_safra, {"safra": c.safra_nome, "ano": c.safra_ano, "custo": 0.0})
        info["custo"] += float(c.custo_total)

    por_safra_severidade: dict[tuple, int] = {}
    safras_ano: dict[int, tuple[str, int]] = {}
    for o in todos_ocorrencias:
        safras_ano[o.id_safra] = (o.safra_nome, o.safra_ano)
        chave = (o.id_safra, o.nivel_severidade or "Nao informado")
        por_safra_severidade[chave] = por_safra_severidade.get(chave, 0) + o.total_ocorrencias

    if len(por_safra_custo) < 2 and len({s for s, _ in [(k[0], k[1]) for k in por_safra_severidade]}) < 2:
        st.info(
            "Ainda ha apenas uma safra com dados — a tendencia entre safras "
            "aparece aqui assim que houver historico de mais de uma safra."
        )
        return

    col_custo, col_ocorr = st.columns(2)
    with col_custo:
        linhas_custo = sorted(por_safra_custo.values(), key=lambda l: l["ano"])
        if linhas_custo:
            df_custo = pd.DataFrame(linhas_custo)
            charts.line_chart(
                df_custo,
                x="safra",
                y="custo",
                y_title="Custo de defensivos (R$)",
                height=260,
            )
    with col_ocorr:
        linhas_ocorr = [
            {
                "safra": safras_ano[id_s][0],
                "ano": safras_ano[id_s][1],
                "severidade": sev,
                "total": total,
            }
            for (id_s, sev), total in por_safra_severidade.items()
        ]
        if linhas_ocorr:
            df_ocorr = pd.DataFrame(linhas_ocorr).sort_values("ano")
            dominio = [s for s in _SEVERITY_ORDER if s in df_ocorr["severidade"].unique()]
            dominio += [s for s in df_ocorr["severidade"].unique() if s not in dominio]
            charts.bar_chart(
                df_ocorr,
                x="safra",
                y="total",
                color="severidade",
                color_map=_SEVERITY_COLORS,
                category_orders={"severidade": dominio},
                barmode="stack",
                y_title="Ocorrencias",
                height=260,
                select_key=None,
            )


def _render_custos(id_safra: int | None, id_talhao: int | None, produtividade_por_talhao: dict) -> None:
    try:
        custos = _client().listar_custos_fitossanidade(id_safra=id_safra, id_talhao=id_talhao)
    except InteligenciaApiError as exc:
        toast_error(exc)
        return

    custo_total = sum(float(i.custo_total) for i in custos)
    total_aplicacoes = sum(i.total_aplicacoes for i in custos)
    talhoes_com_custo = sum(1 for i in custos if i.custo_total)

    col1, col2, col3 = st.columns(3)
    col1.metric("Custo total de defensivos", fmt_brl(custo_total))
    col2.metric("Aplicacoes registradas", fmt_int(total_aplicacoes))
    col3.metric("Talhoes com custo no periodo", fmt_int(talhoes_com_custo))

    if not custos:
        st.info("Sem dados de custo de defensivos para o filtro selecionado.")
        return

    df_chart = pd.DataFrame(
        [
            {"talhao": f"{i.talhao_nome} ({i.safra_nome})", "custo": float(i.custo_total)}
            for i in custos
        ]
    ).sort_values("custo", ascending=False)
    charts.bar_chart(
        df_chart,
        x="talhao",
        y="custo",
        y_title="Custo de defensivos (R$)",
        select_key=None,
    )

    df_tabela = pd.DataFrame(
        [
            {
                "Talhao": i.talhao_nome,
                "Safra": i.safra_nome,
                "Aplicacoes": i.total_aplicacoes,
                "Custo total (R$)": float(i.custo_total),
                "R$/ha": (
                    float(i.custo_total) / produtividade_por_talhao[i.id_talhao]
                    if i.id_talhao in produtividade_por_talhao and produtividade_por_talhao[i.id_talhao]
                    else None
                ),
            }
            for i in custos
        ]
    )
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)
    download_csv(df_tabela, filename="custo_defensivos.csv", key=f"{_PREFIX}_custos_csv")


def _render_ocorrencias(id_safra: int | None, id_talhao: int | None) -> list:
    try:
        ocorrencias = _client().listar_ocorrencias_fitossanidade(
            id_safra=id_safra, id_talhao=id_talhao
        )
    except InteligenciaApiError as exc:
        toast_error(exc)
        return []

    total = sum(i.total_ocorrencias for i in ocorrencias)
    criticas = sum(i.total_ocorrencias for i in ocorrencias if i.nivel_severidade == "Critico")
    altas = sum(i.total_ocorrencias for i in ocorrencias if i.nivel_severidade == "Alto")

    col1, col2, col3 = st.columns(3)
    col1.metric("Ocorrencias registradas", fmt_int(total))
    col2.metric("Severidade critica", fmt_int(criticas))
    col3.metric("Severidade alta", fmt_int(altas))

    if not ocorrencias:
        st.info("Sem ocorrencias de agentes nocivos para o filtro selecionado.")
        return ocorrencias

    df_chart = (
        pd.DataFrame(
            [
                {
                    "talhao": f"{i.talhao_nome} ({i.safra_nome})",
                    "severidade": i.nivel_severidade or "Nao informado",
                    "total": i.total_ocorrencias,
                }
                for i in ocorrencias
            ]
        )
        .groupby(["talhao", "severidade"], as_index=False)["total"]
        .sum()
    )
    dominio = [s for s in _SEVERITY_ORDER if s in df_chart["severidade"].unique()]
    dominio += [s for s in df_chart["severidade"].unique() if s not in dominio]
    charts.bar_chart(
        df_chart,
        x="talhao",
        y="total",
        color="severidade",
        color_map=_SEVERITY_COLORS,
        category_orders={"severidade": dominio},
        barmode="stack",
        y_title="Ocorrencias",
        select_key=None,
    )

    col_tabela, col_ranking = st.columns(2)
    with col_tabela:
        df_tabela = pd.DataFrame(
            [
                {
                    "Talhao": i.talhao_nome,
                    "Safra": i.safra_nome,
                    "Severidade": i.nivel_severidade or "Nao informado",
                    "Agente": i.agente_nome or "-",
                    "Ocorrencias": i.total_ocorrencias,
                }
                for i in ocorrencias
            ]
        )
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
        download_csv(df_tabela, filename="ocorrencias_fitossanidade.csv", key=f"{_PREFIX}_ocorr_csv")
    with col_ranking:
        st.caption("Top agentes ofensores no filtro selecionado")
        df_agentes = (
            pd.DataFrame(
                [
                    {"agente": i.agente_nome or "Nao informado", "total": i.total_ocorrencias}
                    for i in ocorrencias
                ]
            )
            .groupby("agente", as_index=False)["total"]
            .sum()
            .sort_values("total", ascending=False)
            .head(10)
        )
        charts.bar_chart(
            df_agentes,
            x="agente",
            y="total",
            y_title="Ocorrencias",
            height=280,
            select_key=None,
        )

    return ocorrencias


def _render_pressao_x_produtividade(ocorrencias: list, id_safra: int | None, id_talhao: int | None) -> None:
    st.caption(
        "Cada ponto e um talhao: cruza o total de ocorrencias de severidade "
        "Alta/Critica com a variacao de produtividade vs. meta (modulo "
        "Producao) — ajuda a ver se pressao fitossanitaria explica quedas "
        "de produtividade."
    )
    try:
        produtividade = _client().listar_produtividade(id_safra=id_safra, id_talhao=id_talhao)
    except InteligenciaApiError as exc:
        toast_error(exc)
        return

    pressao_por_talhao: dict[int, int] = {}
    for o in ocorrencias:
        if o.nivel_severidade in _PRESSAO_ALTA:
            pressao_por_talhao[o.id_talhao] = pressao_por_talhao.get(o.id_talhao, 0) + o.total_ocorrencias

    linhas = []
    for p in produtividade:
        if p.variacao_percentual is None:
            continue
        linhas.append(
            {
                "Talhao": f"{p.talhao_nome} ({p.safra_nome})",
                "Ocorrencias Alto/Critico": pressao_por_talhao.get(p.id_talhao, 0),
                "Variacao de produtividade (%)": float(p.variacao_percentual),
            }
        )

    if not linhas:
        st.info(
            "Sem talhoes com meta e producao realizada simultaneamente no "
            "filtro selecionado para cruzar com a pressao fitossanitaria."
        )
        return

    df = pd.DataFrame(linhas)
    charts.scatter_chart(
        df,
        x="Ocorrencias Alto/Critico",
        y="Variacao de produtividade (%)",
        hover_name="Talhao",
        height=300,
    )


def render() -> None:
    setup_page(
        "Fitossanidade",
        "Custo de defensivos e ocorrencias de agentes nocivos, cruzados com produtividade.",
    )

    try:
        todos_custos = _client().listar_custos_fitossanidade()
        todos_ocorrencias = _client().listar_ocorrencias_fitossanidade()
        todos_produtividade = _client().listar_produtividade()
    except InteligenciaApiError as exc:
        toast_error(exc)
        st.stop()

    st.subheader("Visao geral — todas as safras")
    _render_visao_geral(todos_custos, todos_ocorrencias)

    st.divider()

    id_safra, id_talhao = _render_filtros()
    area_por_talhao = {
        p.id_talhao: float(p.area_hectares) for p in todos_produtividade if p.area_hectares
    }

    st.subheader("Custo de defensivos")
    _render_custos(id_safra, id_talhao, area_por_talhao)

    st.divider()

    st.subheader("Ocorrencias por severidade")
    ocorrencias_filtro = _render_ocorrencias(id_safra, id_talhao)

    st.divider()

    st.subheader("Pressao fitossanitaria x produtividade")
    _render_pressao_x_produtividade(ocorrencias_filtro, id_safra, id_talhao)
