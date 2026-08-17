"""Comercial — vendas, clientes, produtos e catálogo."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import pandas as pd
import streamlit as st

from components.comercial import catalogo_dialogs, clientes_dialogs, produtos_dialogs, vendas_dialogs
from components.comercial.catalogo_tables import categorias_df, centros_custo_df, certificacoes_df, unidades_df
from components.comercial.clientes_tables import clientes_df
from components.comercial.dialog_state import open_dialog
from components.comercial.formatters import cliente_label
from components.comercial.produtos_tables import produtos_df
from components.comercial.vendas_tables import vendas_df
from components.shared.screens import (
    crud_toolbar,
    data_table,
    filter_dataframe,
    row_actions,
    setup_page,
    toast_error,
    toast_ok,
)
from services.comercial_client import (
    ComercialApiError,
    ComercialClient,
    CotacaoAgroDocSyncRequest,
)
from services.financeiro_client import FinanceiroApiError, FinanceiroClient
from services.identity_client import require_login
from services.inteligencia_client import InteligenciaApiError, InteligenciaClient

require_login()

setup_page("Comercial", "Vendas, clientes, produtos e catálogo comercial.")


def _client() -> ComercialClient:
    return ComercialClient()


def _financeiro_client() -> FinanceiroClient:
    return FinanceiroClient()


def _inteligencia_client() -> InteligenciaClient:
    return InteligenciaClient()


# Palavra-chave no nome do produto cadastrado -> nome do produto na cotacao AgroDoc
_COTACAO_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("boi", "Boi Gordo CEPEA/SP"),
    ("vaca", "Vaca Gorda"),
    ("soja", "Soja"),
    ("milho", "Milho"),
    ("bezerro", "Bezerro MS"),
)


def _cotacao_correspondente(nome_produto: str, cotacoes):
    nome_lower = nome_produto.lower()
    for keyword, produto_agrodoc in _COTACAO_KEYWORDS:
        if keyword in nome_lower:
            return next((c for c in cotacoes if c.product == produto_agrodoc), None)
    return None


def _comparativo_cotacoes_df(produtos, cotacoes) -> tuple[pd.DataFrame, list[str]]:
    """Compara o preco cadastrado de cada produto com a cotacao AgroDoc equivalente."""
    linhas = []
    sem_referencia = []
    for produto in produtos:
        cotacao_ref = _cotacao_correspondente(produto.nome, cotacoes)
        if cotacao_ref is None:
            sem_referencia.append(produto.nome)
            continue
        if produto.preco is None:
            sem_referencia.append(produto.nome)
            continue

        preco_cadastrado = float(produto.preco)
        preco_agrodoc = float(cotacao_ref.price)
        diferenca = preco_cadastrado - preco_agrodoc
        diferenca_pct = (diferenca / preco_agrodoc * 100) if preco_agrodoc else None

        linhas.append(
            {
                "Produto cadastrado": produto.nome,
                "Preço cadastrado (R$)": round(preco_cadastrado, 2),
                "Referência AgroDoc": cotacao_ref.product,
                "Cotação AgroDoc (R$)": round(preco_agrodoc, 2),
                "Unidade AgroDoc": cotacao_ref.unit or "—",
                "Diferença (R$)": round(diferenca, 2),
                "Diferença (%)": (
                    round(diferenca_pct, 1) if diferenca_pct is not None else pd.NA
                ),
            }
        )
    return pd.DataFrame(linhas), sem_referencia


tab_vendas, tab_clientes, tab_produtos, tab_catalogo, tab_cotacoes = st.tabs(
    ["Vendas", "Clientes", "Produtos", "Catálogo", "Cotações"]
)


# ----------------------------------------------------------------------
# Vendas (sem edição avulsa — nasce completa via "Nova venda")
# ----------------------------------------------------------------------
with tab_vendas:
    try:
        vendas = _client().list_vendas()
        clientes_opt = _client().list_cliente_options()
    except ComercialApiError as exc:
        toast_error(exc)
        st.stop()

    cliente_por_id = {c.id_cliente: cliente_label(c) for c in clientes_opt}

    try:
        contas_receber = _financeiro_client().list_contas_receber(limit=500)
        conta_por_venda = {c.id_venda: c for c in contas_receber if c.id_venda is not None}
    except FinanceiroApiError:
        conta_por_venda = {}
        st.caption(
            "Nao foi possivel carregar o status de recebimento do Financeiro agora."
        )

    if vendas:
        total_valor = sum(float(v.valor_total) for v in vendas)
        total_a_receber = sum(
            float(c.saldo) for c in conta_por_venda.values() if c.saldo
        )
        vencidas = sum(1 for c in conta_por_venda.values() if c.status == "VENCIDA")
        c1, c2, c3 = st.columns(3)
        c1.metric("Vendas", len(vendas))
        c2.metric("Total vendido", f"R$ {total_valor:,.2f}")
        c3.metric("A receber (com vencidas)", f"R$ {total_a_receber:,.2f}", delta=f"{vencidas} vencida(s)" if vencidas else None, delta_color="inverse")
        st.divider()

    query, new_clicked = crud_toolbar(key="vendas", filter_placeholder="Filtrar vendas...", new_label="Nova venda")
    if new_clicked:
        open_dialog("vendas", "create")

    df = filter_dataframe(vendas_df(vendas, cliente_por_id, conta_por_venda), query)
    selected = data_table(df, key="vendas_grid")
    action = row_actions(key="vendas", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

    if action == "view" and selected:
        open_dialog("vendas", "view", int(selected[0]["ID"]))

    vendas_dialogs.render("vendas")


# ----------------------------------------------------------------------
# Clientes
# ----------------------------------------------------------------------
with tab_clientes:
    try:
        clientes = _client().list_clientes()
    except ComercialApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(key="clientes", filter_placeholder="Filtrar clientes...", new_label="Novo")
    if new_clicked:
        open_dialog("clientes", "create")

    df = filter_dataframe(clientes_df(clientes), query)
    selected = data_table(df, key="clientes_grid")
    action = row_actions(key="clientes", selected_count=len(selected), total_count=len(df), disabled=not selected)

    if action == "view" and selected:
        open_dialog("clientes", "view", int(selected[0]["ID"]))
    elif action == "edit" and selected:
        open_dialog("clientes", "edit", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("clientes", "delete", int(selected[0]["ID"]))

    clientes_dialogs.render("clientes")


# ----------------------------------------------------------------------
# Produtos
# ----------------------------------------------------------------------
with tab_produtos:
    try:
        produtos = _client().list_produtos()
    except ComercialApiError as exc:
        toast_error(exc)
        st.stop()

    query, new_clicked = crud_toolbar(key="produtos", filter_placeholder="Filtrar produtos...", new_label="Novo")
    if new_clicked:
        open_dialog("produtos", "create")

    df = filter_dataframe(produtos_df(produtos), query)
    selected = data_table(df, key="produtos_grid")
    action = row_actions(key="produtos", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

    if action == "view" and selected:
        open_dialog("produtos", "view", int(selected[0]["ID"]))
    elif action == "delete" and selected:
        open_dialog("produtos", "delete", int(selected[0]["ID"]))

    produtos_dialogs.render("produtos")


# ----------------------------------------------------------------------
# Catálogo (categorias, unidades de medida, certificações)
# ----------------------------------------------------------------------
with tab_catalogo:
    sub_categorias, sub_unidades, sub_certificacoes, sub_centros_custo = st.tabs(
        ["Categorias", "Unidades de medida", "Certificações", "Centros de custo"]
    )

    with sub_categorias:
        try:
            categorias = _client().list_categorias_produto()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(key="categorias", filter_placeholder="Filtrar categorias...", new_label="Nova")
        if new_clicked:
            open_dialog("categorias", "create")

        df = filter_dataframe(categorias_df(categorias), query)
        selected = data_table(df, key="categorias_grid")
        action = row_actions(key="categorias", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

        if action == "delete" and selected:
            open_dialog("categorias", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("categorias")

    with sub_unidades:
        try:
            unidades = _client().list_unidades_medida()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(key="unidades", filter_placeholder="Filtrar unidades...", new_label="Nova")
        if new_clicked:
            open_dialog("unidades", "create")

        df = filter_dataframe(unidades_df(unidades), query)
        selected = data_table(df, key="unidades_grid")
        action = row_actions(key="unidades", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False)

        if action == "delete" and selected:
            open_dialog("unidades", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("unidades")

    with sub_certificacoes:
        try:
            certificacoes = _client().list_certificacoes()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(
            key="certificacoes_comercial", filter_placeholder="Filtrar certificações...", new_label="Nova"
        )
        if new_clicked:
            open_dialog("certificacoes", "create")

        df = filter_dataframe(certificacoes_df(certificacoes), query)
        selected = data_table(df, key="certificacoes_comercial_grid")
        action = row_actions(
            key="certificacoes_comercial", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False
        )

        if action == "delete" and selected:
            open_dialog("certificacoes", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("certificacoes")

    with sub_centros_custo:
        try:
            centros_custo = _client().list_centro_custo_options()
        except ComercialApiError as exc:
            toast_error(exc)
            st.stop()

        query, new_clicked = crud_toolbar(
            key="centros_custo", filter_placeholder="Filtrar centros de custo...", new_label="Novo"
        )
        if new_clicked:
            open_dialog("centros_custo", "create")

        df = filter_dataframe(centros_custo_df(centros_custo), query)
        selected = data_table(df, key="centros_custo_grid")
        action = row_actions(
            key="centros_custo", selected_count=len(selected), total_count=len(df), disabled=not selected, show_edit=False
        )

        if action == "delete" and selected:
            open_dialog("centros_custo", "delete", int(selected[0]["ID"]))

        catalogo_dialogs.render("centros_custo")


# ----------------------------------------------------------------------
# Cotações de mercado — comparativo entre preço cadastrado e AgroDoc/CEPEA
# ----------------------------------------------------------------------
with tab_cotacoes:
    st.caption(
        "Compara o preço cadastrado de cada produto com a cotação de mercado "
        "equivalente (CEPEA/ESALQ via AgroDoc), para saber se o preço praticado "
        "está acima ou abaixo do mercado."
    )

    try:
        produtos_cotacao = _client().list_produtos()
    except ComercialApiError as exc:
        toast_error(exc)
        produtos_cotacao = []

    try:
        cotacoes_atuais = _inteligencia_client().get_cotacao_atual()
    except InteligenciaApiError as exc:
        st.warning(f"Não foi possível consultar a cotação AgroDoc agora: {exc.user_message}")
        cotacoes_atuais = []

    if not produtos_cotacao:
        st.info("Cadastre produtos na aba 'Produtos' para comparar com a cotação de mercado.")
    elif not cotacoes_atuais:
        st.info("Cotação AgroDoc indisponível no momento.")
    else:
        df_comparativo, sem_referencia = _comparativo_cotacoes_df(produtos_cotacao, cotacoes_atuais)

        if df_comparativo.empty:
            st.info(
                "Nenhum produto cadastrado corresponde às commodities monitoradas pelo "
                "AgroDoc (boi, vaca, soja, milho, bezerro)."
            )
        else:
            acima = int((df_comparativo["Diferença (R$)"] > 0).sum())
            abaixo = int((df_comparativo["Diferença (R$)"] < 0).sum())
            c1, c2, c3 = st.columns(3)
            c1.metric("Produtos comparados", len(df_comparativo))
            c2.metric("Acima do mercado", acima)
            c3.metric("Abaixo do mercado", abaixo)

            data_table(df_comparativo, key="comparativo_cotacoes")

        if sem_referencia:
            st.caption(
                "Sem cotação de referência ou sem preço cadastrado: "
                + ", ".join(sem_referencia)
            )

    st.divider()
    st.markdown("**Sincronizar cotações no histórico de indicadores (Inteligência)**")
    col_uf, col_safra, col_botao = st.columns([2, 2, 1])
    with col_uf:
        uf_opcoes = ("Nenhuma",) + (
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
            "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
            "SP", "SE", "TO",
        )
        uf_escolha = st.selectbox("UF (preço regional do boi)", uf_opcoes, key="comercial_cotacao_uf")
    with col_safra:
        id_safra_input = st.number_input(
            "Associar a safra (ID, opcional)",
            min_value=0,
            step=1,
            value=0,
            key="comercial_cotacao_safra",
        )
    with col_botao:
        st.write("")
        sincronizar_clicked = st.button(
            "Sincronizar",
            type="primary",
            icon=":material/sync:",
            use_container_width=True,
            key="comercial_cotacao_sync_btn",
        )

    if sincronizar_clicked:
        try:
            ids_medicao = _client().sync_cotacao_agrodoc(
                CotacaoAgroDocSyncRequest(
                    uf=None if uf_escolha == "Nenhuma" else uf_escolha,
                    id_safra=int(id_safra_input) or None,
                    data_referencia=date.today(),
                )
            )
            toast_ok(f"{len(ids_medicao)} cotações registradas em Inteligência.")
            st.rerun()
        except ComercialApiError as exc:
            toast_error(exc)
