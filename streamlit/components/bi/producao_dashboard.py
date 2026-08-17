"""BI dashboard for agricultural productivity (kg/ha, planned x realized).

Alem do recorte por talhao/safra, cruza produtividade com custo de
defensivos (modulo Fitossanidade/Financeiro), clima (Open-Meteo, via
Inteligencia > Clima) e cotacao de mercado (AgroDoc/CEPEA, via
Inteligencia > Cotacao) para dar uma visao global da safra.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.bi import charts
from components.bi.widgets import download_csv, fmt_brl, fmt_int, fmt_qty
from components.shared.screens import setup_page, toast_error
from services import producao_client as producao_api
from services.inteligencia_client import InteligenciaApiError, InteligenciaClient

_TEAL, _AMBER = "#0E8C7D", "#C9861E"
_PREFIX = "bi_producao"


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


def _fmt_kgha(valor) -> str:
    return f"{fmt_qty(float(valor))} kg/ha" if valor is not None else "—"


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


def _render_visao_geral(todos: list) -> None:
    st.caption(
        "Evolucao da produtividade media da fazenda ao longo das safras "
        "(independente do filtro abaixo)."
    )
    por_safra: dict[int, dict] = {}
    for i in todos:
        info = por_safra.setdefault(
            i.id_safra,
            {"safra": i.safra_nome, "ano": i.safra_ano, "realizados": [], "colhido": 0.0, "talhoes": set()},
        )
        info["talhoes"].add(i.id_talhao)
        if i.produtividade_realizada is not None:
            info["realizados"].append(float(i.produtividade_realizada))
        if i.quantidade_colhida_total is not None:
            info["colhido"] += float(i.quantidade_colhida_total)

    linhas = [
        {
            "safra": info["safra"],
            "ano": info["ano"],
            "produtividade_media": (
                sum(info["realizados"]) / len(info["realizados"]) if info["realizados"] else None
            ),
            "colhido_total": info["colhido"],
            "talhoes": len(info["talhoes"]),
        }
        for info in por_safra.values()
    ]
    linhas.sort(key=lambda l: l["ano"])

    if len(linhas) < 2:
        st.info(
            "Ainda ha apenas uma safra com dados — a tendencia entre safras "
            "aparece aqui assim que houver historico de mais de uma safra."
        )
        return

    df = pd.DataFrame(linhas)
    col_chart, col_kpi = st.columns([3, 1])
    with col_chart:
        charts.line_chart(
            df.dropna(subset=["produtividade_media"]),
            x="safra",
            y="produtividade_media",
            x_title=None,
            y_title="Produtividade media (kg/ha)",
            height=260,
        )
    with col_kpi:
        atual, anterior = linhas[-1], linhas[-2]
        if atual["produtividade_media"] is not None and anterior["produtividade_media"]:
            delta_pct = (
                (atual["produtividade_media"] - anterior["produtividade_media"])
                / anterior["produtividade_media"]
                * 100
            )
            st.metric(
                f"{atual['safra']} vs. {anterior['safra']}",
                _fmt_kgha(atual["produtividade_media"]),
                delta=f"{delta_pct:+.1f}%",
            )
        st.metric("Safras com historico", fmt_int(len(linhas)))


def _render_custo_eficiencia(itens: list, id_safra: int | None, id_talhao: int | None) -> None:
    st.caption(
        "Custo de defensivos (Fitossanidade/Financeiro) por kg colhido e por "
        "hectare — quanto maior o R$/kg, menos eficiente o talhao no periodo."
    )
    try:
        custos = _client().listar_custos_fitossanidade(id_safra=id_safra, id_talhao=id_talhao)
    except InteligenciaApiError as exc:
        toast_error(exc)
        return

    custo_por_talhao = {c.id_talhao: c for c in custos}
    linhas = []
    for i in itens:
        custo = custo_por_talhao.get(i.id_talhao)
        if custo is None:
            continue
        custo_total = float(custo.custo_total)
        colhido = float(i.quantidade_colhida_total) if i.quantidade_colhida_total else None
        area = float(i.area_hectares) if i.area_hectares else None
        linhas.append(
            {
                "Talhao": i.talhao_nome,
                "Safra": i.safra_nome,
                "Custo total (R$)": custo_total,
                "R$/kg": (custo_total / colhido) if colhido else None,
                "R$/ha": (custo_total / area) if area else None,
                "Realizado (kg/ha)": (
                    float(i.produtividade_realizada) if i.produtividade_realizada is not None else None
                ),
            }
        )

    if not linhas:
        st.info("Sem custo de defensivos registrado para o filtro selecionado.")
        return

    df = pd.DataFrame(linhas)
    st.dataframe(df, use_container_width=True, hide_index=True)

    com_custo_kg = df.dropna(subset=["R$/kg"])
    if not com_custo_kg.empty:
        charts.scatter_chart(
            com_custo_kg,
            x="R$/kg",
            y="Realizado (kg/ha)",
            hover_name="Talhao",
            x_title="Custo de defensivos por kg colhido (R$)",
            y_title="Produtividade realizada (kg/ha)",
            height=280,
        )


def _render_clima_correlacao(todos: list) -> None:
    st.caption(
        "Cruza a produtividade media de cada safra com o clima registrado em "
        "Inteligencia > Clima (sincronizado via Open-Meteo). Sincronize o "
        "clima de mais safras para enriquecer esta visao."
    )
    try:
        indicadores = _client().list_indicadores()
    except InteligenciaApiError as exc:
        toast_error(exc)
        return

    id_precip = next((i.id_indicador for i in indicadores if "precipita" in i.nome.lower()), None)
    id_temp = next((i.id_indicador for i in indicadores if "temperatura" in i.nome.lower()), None)

    if id_precip is None and id_temp is None:
        st.info(
            "Nenhuma medicao de clima registrada ainda. Use a aba "
            "Inteligencia > Clima para sincronizar e associar a uma safra."
        )
        return

    por_safra: dict[int, dict] = {}
    for id_indicador, campo in ((id_precip, "precipitacao_mm"), (id_temp, "temperatura_c")):
        if id_indicador is None:
            continue
        try:
            medicoes = _client().list_medicoes(id_indicador=id_indicador)
        except InteligenciaApiError:
            continue
        for m in medicoes:
            if m.id_safra is None or m.valor is None:
                continue
            info = por_safra.setdefault(m.id_safra, {"safra": m.safra_nome or f"Safra {m.id_safra}"})
            info[campo] = float(m.valor)

    produtividade_por_safra: dict[int, list[float]] = {}
    for i in todos:
        if i.produtividade_realizada is not None:
            produtividade_por_safra.setdefault(i.id_safra, []).append(float(i.produtividade_realizada))

    linhas = []
    for id_s, dados in por_safra.items():
        realizados = produtividade_por_safra.get(id_s)
        if not realizados:
            continue
        linhas.append(
            {
                "Safra": dados["safra"],
                "Precipitacao (mm)": dados.get("precipitacao_mm"),
                "Temperatura (C)": dados.get("temperatura_c"),
                "Produtividade media (kg/ha)": sum(realizados) / len(realizados),
            }
        )

    if not linhas:
        st.info(
            "Ainda nao ha safra com clima sincronizado e colheita registrada "
            "ao mesmo tempo para cruzar."
        )
        return

    df = pd.DataFrame(linhas)
    st.dataframe(df, use_container_width=True, hide_index=True)

    com_precip = df.dropna(subset=["Precipitacao (mm)"])
    if len(com_precip) >= 1:
        charts.scatter_chart(
            com_precip,
            x="Precipitacao (mm)",
            y="Produtividade media (kg/ha)",
            hover_name="Safra",
            height=280,
        )


def _render_cotacao_contexto(itens: list) -> None:
    st.caption(
        "Cotacao de mercado atual (AgroDoc/CEPEA) das culturas presentes no "
        "filtro — referencia externa, sem conversao de unidade/safra."
    )
    culturas = sorted({i.cultura_nome for i in itens if i.cultura_nome})
    if not culturas:
        st.info("Sem cultura associada aos talhoes do filtro (defina em Planejamento de safra).")
        return

    try:
        cotacoes = _client().get_cotacao_atual()
    except InteligenciaApiError as exc:
        toast_error(exc)
        return

    cotacao_por_produto = {c.product.lower(): c for c in cotacoes}
    encontrados = [
        (cultura, cotacao_por_produto[cultura.lower()])
        for cultura in culturas
        if cultura.lower() in cotacao_por_produto
    ]
    if not encontrados:
        st.info(
            "Nenhuma das culturas do filtro tem cotacao disponivel no momento "
            f"({', '.join(culturas)})."
        )
        return

    cols = st.columns(len(encontrados))
    for col, (cultura, cotacao) in zip(cols, encontrados):
        unidade = f" / {cotacao.unit}" if cotacao.unit else ""
        col.metric(cultura, f"{fmt_brl(float(cotacao.price))}{unidade}")


def render() -> None:
    setup_page(
        "Produtividade",
        "Produtividade realizada (kg/ha) x meta planejada, tendencias e cruzamento com clima/mercado.",
    )

    try:
        todos = _client().listar_produtividade()
    except InteligenciaApiError as exc:
        toast_error(exc)
        st.stop()

    st.subheader("Visao geral — todas as safras")
    _render_visao_geral(todos)

    st.divider()

    id_safra, id_talhao = _render_filtros()
    itens = [
        i
        for i in todos
        if (id_safra is None or i.id_safra == id_safra)
        and (id_talhao is None or i.id_talhao == id_talhao)
    ]

    com_realizado = [i for i in itens if i.produtividade_realizada is not None]
    com_meta_e_realizado = [i for i in com_realizado if i.meta_produtividade]
    media_realizada = (
        sum(float(i.produtividade_realizada) for i in com_realizado) / len(com_realizado)
        if com_realizado
        else None
    )
    media_variacao = (
        sum(float(i.variacao_percentual) for i in com_meta_e_realizado)
        / len(com_meta_e_realizado)
        if com_meta_e_realizado
        else None
    )
    abaixo_meta = sum(1 for i in com_meta_e_realizado if float(i.variacao_percentual) < 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Produtividade media realizada", _fmt_kgha(media_realizada))
    col2.metric(
        "Variacao media vs. meta",
        f"{media_variacao:+.1f}%" if media_variacao is not None else "—",
    )
    col3.metric("Talhoes abaixo da meta", fmt_int(abaixo_meta))

    st.divider()

    linhas_chart = []
    for i in itens:
        rotulo = f"{i.talhao_nome} ({i.safra_nome})"
        if i.meta_produtividade is not None:
            linhas_chart.append(
                {"talhao": rotulo, "tipo": "Meta planejada", "kg/ha": float(i.meta_produtividade)}
            )
        if i.produtividade_realizada is not None:
            linhas_chart.append(
                {"talhao": rotulo, "tipo": "Realizado", "kg/ha": float(i.produtividade_realizada)}
            )
    df_chart = pd.DataFrame(linhas_chart)
    charts.bar_chart(
        df_chart,
        x="talhao",
        y="kg/ha",
        color="tipo",
        color_map={"Meta planejada": _AMBER, "Realizado": _TEAL},
        barmode="group",
        y_title="Produtividade (kg/ha)",
        select_key=None,
    )

    st.divider()

    if not itens:
        st.info("Nenhum talhao encontrado para o filtro selecionado.")
        return

    df_tabela = pd.DataFrame(
        [
            {
                "Talhao": i.talhao_nome,
                "Safra": i.safra_nome,
                "Cultura": i.cultura_nome or "-",
                "Area (ha)": float(i.area_hectares) if i.area_hectares is not None else None,
                "Meta (kg/ha)": float(i.meta_produtividade) if i.meta_produtividade is not None else None,
                "Colhido total (kg)": (
                    float(i.quantidade_colhida_total)
                    if i.quantidade_colhida_total is not None
                    else None
                ),
                "Realizado (kg/ha)": (
                    float(i.produtividade_realizada)
                    if i.produtividade_realizada is not None
                    else None
                ),
                "Variacao (%)": (
                    float(i.variacao_percentual) if i.variacao_percentual is not None else None
                ),
            }
            for i in itens
        ]
    )
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)
    download_csv(df_tabela, filename="produtividade.csv", key=f"{_PREFIX}_csv")

    criticos = [i for i in itens if i.variacao_percentual is not None and i.variacao_percentual <= -20]
    if criticos:
        nomes = ", ".join(f"{i.talhao_nome} ({i.variacao_percentual:+.1f}%)" for i in criticos)
        st.error(f"Talhoes 20% ou mais abaixo da meta: {nomes}")

    st.divider()
    st.subheader("Custo de defensivos x produtividade")
    _render_custo_eficiencia(itens, id_safra, id_talhao)

    st.divider()
    st.subheader("Clima x produtividade, por safra")
    _render_clima_correlacao(todos)

    st.divider()
    st.subheader("Cotacao de mercado das culturas do filtro")
    _render_cotacao_contexto(itens)
