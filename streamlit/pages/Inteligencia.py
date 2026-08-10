"""Inteligencia — indicadores, medicoes e agregacao basica."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import pandas as pd
import streamlit as st

from app.inteligencia.schemas import (
    ClimaSyncRequestSchema,
    IndicadorCreateSchema,
    IndicadorUpdateSchema,
    MedicaoIndicadorCreateSchema,
    MedicaoIndicadorUpdateSchema,
)
from components.shared import clima
from components.shared.screens import data_table, setup_page, toast_error, toast_ok
from services import producao_client as producao_api
from services.identity_client import require_login
from services.inteligencia_client import InteligenciaApiError, InteligenciaClient


def _client() -> InteligenciaClient:
    return InteligenciaClient()


@st.cache_data(ttl=15)
def _listar_safras() -> list[dict]:
    return producao_api.listar("/safras")


def _label_indicador(item: dict) -> str:
    unidade = item.get("unidade")
    sufixo = f" ({unidade})" if unidade else ""
    return f"#{item['id_indicador']} - {item['nome']}{sufixo}"


def _label_safra(item: dict) -> str:
    return f"#{item['id_safra']} - {item['nome']} ({item.get('ano', '')})"


def _render_indicadores() -> None:
    with st.expander("Filtros", expanded=False):
        filtro_nome = st.text_input("Nome contem", key="filtro_ind_nome")
        filtro_unidade = st.text_input("Unidade", key="filtro_ind_unidade")

    try:
        indicadores = _client().list_indicadores(
            nome=filtro_nome or None,
            unidade=filtro_unidade or None,
        )
    except InteligenciaApiError as exc:
        toast_error(exc)
        indicadores = []

    if indicadores:
        data_table(
            pd.DataFrame([i.model_dump() for i in indicadores]),
            key="indicadores",
        )
    else:
        st.info("Nenhum indicador encontrado.")

    st.divider()
    col_novo, col_editar = st.columns(2)

    with col_novo:
        st.markdown("**Novo indicador**")
        with st.form("form_novo_indicador"):
            nome = st.text_input("Nome")
            unidade = st.text_input("Unidade (opcional)")
            criar = st.form_submit_button("Cadastrar")

        if criar:
            if not nome.strip():
                st.error("Informe o nome do indicador.")
            else:
                try:
                    _client().create_indicador(
                        IndicadorCreateSchema(
                            nome=nome.strip(),
                            unidade=unidade.strip() or None,
                        )
                    )
                    toast_ok("Indicador cadastrado.")
                    st.rerun()
                except InteligenciaApiError as exc:
                    toast_error(exc)

    with col_editar:
        st.markdown("**Editar / excluir**")
        if not indicadores:
            st.caption("Cadastre um indicador para editar.")
            return

        opcoes = {f"#{i.id_indicador} - {i.nome}": i for i in indicadores}
        selecionado = st.selectbox("Indicador", list(opcoes.keys()), key="sel_indicador")
        indicador = opcoes[selecionado]

        with st.form("form_editar_indicador"):
            novo_nome = st.text_input("Nome", value=indicador.nome)
            nova_unidade = st.text_input(
                "Unidade",
                value=indicador.unidade or "",
            )
            salvar = st.form_submit_button("Salvar alteracoes")

        if salvar:
            try:
                _client().update_indicador(
                    indicador.id_indicador,
                    IndicadorUpdateSchema(
                        nome=novo_nome.strip(),
                        unidade=nova_unidade.strip() or None,
                    ),
                )
                toast_ok("Indicador atualizado.")
                st.rerun()
            except InteligenciaApiError as exc:
                toast_error(exc)

        if st.button("Excluir indicador", type="secondary"):
            try:
                _client().delete_indicador(indicador.id_indicador)
                toast_ok("Indicador excluido.")
                st.rerun()
            except InteligenciaApiError as exc:
                toast_error(exc)


def _render_medicoes() -> None:
    try:
        indicadores = _client().list_indicadores()
        safras = _listar_safras()
    except InteligenciaApiError as exc:
        toast_error(exc)
        return
    except Exception as exc:
        st.error(f"Nao foi possivel carregar dados auxiliares: {exc}")
        return

    with st.expander("Filtros", expanded=False):
        filtro_ind = st.number_input(
            "ID indicador",
            min_value=0,
            step=1,
            value=0,
            key="filtro_med_ind",
        )
        filtro_safra = st.number_input(
            "ID safra",
            min_value=0,
            step=1,
            value=0,
            key="filtro_med_safra",
        )
        filtro_inicio = st.date_input(
            "Data inicio",
            value=None,
            key="filtro_med_inicio",
        )
        filtro_fim = st.date_input(
            "Data fim",
            value=None,
            key="filtro_med_fim",
        )

    try:
        medicoes = _client().list_medicoes(
            id_indicador=filtro_ind or None,
            id_safra=filtro_safra or None,
            data_inicio=filtro_inicio,
            data_fim=filtro_fim,
        )
    except InteligenciaApiError as exc:
        toast_error(exc)
        medicoes = []

    if medicoes:
        data_table(
            pd.DataFrame([m.model_dump() for m in medicoes]),
            key="medicoes",
        )
    else:
        st.info("Nenhuma medicao encontrada.")

    st.divider()
    col_nova, col_editar = st.columns(2)

    with col_nova:
        st.markdown("**Nova medicao**")
        if not indicadores:
            st.warning("Cadastre ao menos um indicador.")
        elif not safras:
            st.warning("Cadastre ao menos uma safra em Producao.")
        else:
            mapa_ind = {_label_indicador(i.model_dump()): i.id_indicador for i in indicadores}
            mapa_safra = {_label_safra(s): s["id_safra"] for s in safras}

            with st.form("form_nova_medicao"):
                ind_escolha = st.selectbox("Indicador", list(mapa_ind.keys()))
                safra_escolha = st.selectbox("Safra", list(mapa_safra.keys()))
                valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
                data_ref = st.date_input("Data referencia", value=date.today())
                criar = st.form_submit_button("Registrar")

            if criar:
                try:
                    _client().create_medicao(
                        MedicaoIndicadorCreateSchema(
                            id_indicador=mapa_ind[ind_escolha],
                            id_safra=mapa_safra[safra_escolha],
                            valor=Decimal(str(valor)),
                            data_referencia=data_ref,
                        )
                    )
                    toast_ok("Medicao registrada.")
                    st.rerun()
                except InteligenciaApiError as exc:
                    toast_error(exc)

    with col_editar:
        st.markdown("**Editar / excluir**")
        if not medicoes:
            st.caption("Registre uma medicao para editar.")
            return

        opcoes = {
            f"#{m.id_medicao} - {m.indicador_nome or m.id_indicador} / "
            f"{m.data_referencia}": m
            for m in medicoes
        }
        selecionada = st.selectbox("Medicao", list(opcoes.keys()), key="sel_medicao")
        medicao = opcoes[selecionada]

        with st.form("form_editar_medicao"):
            novo_valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=float(medicao.valor or 0),
            )
            nova_data = st.date_input(
                "Data referencia",
                value=medicao.data_referencia or date.today(),
            )
            salvar = st.form_submit_button("Salvar alteracoes")

        if salvar:
            try:
                _client().update_medicao(
                    medicao.id_medicao,
                    MedicaoIndicadorUpdateSchema(
                        valor=Decimal(str(novo_valor)),
                        data_referencia=nova_data,
                    ),
                )
                toast_ok("Medicao atualizada.")
                st.rerun()
            except InteligenciaApiError as exc:
                toast_error(exc)

        if st.button("Excluir medicao", type="secondary"):
            try:
                _client().delete_medicao(medicao.id_medicao)
                toast_ok("Medicao excluida.")
                st.rerun()
            except InteligenciaApiError as exc:
                toast_error(exc)


def _render_agregacao() -> None:
    try:
        indicadores = _client().list_indicadores()
        safras = _listar_safras()
    except InteligenciaApiError as exc:
        toast_error(exc)
        return
    except Exception as exc:
        st.error(f"Nao foi possivel carregar dados: {exc}")
        return

    if not indicadores:
        st.warning("Cadastre indicadores antes de consultar agregacoes.")
        return

    mapa_ind = {_label_indicador(i.model_dump()): i.id_indicador for i in indicadores}
    mapa_safra = {"Todas": None}
    mapa_safra.update({_label_safra(s): s["id_safra"] for s in safras})

    col1, col2 = st.columns(2)
    with col1:
        ind_escolha = st.selectbox("Indicador", list(mapa_ind.keys()), key="agg_ind")
        safra_escolha = st.selectbox("Safra", list(mapa_safra.keys()), key="agg_safra")
    with col2:
        data_inicio = st.date_input("Data inicio", value=None, key="agg_inicio")
        data_fim = st.date_input("Data fim", value=None, key="agg_fim")

    if st.button("Calcular agregacao", type="primary"):
        try:
            resultado = _client().agregar_medicoes(
                mapa_ind[ind_escolha],
                id_safra=mapa_safra[safra_escolha],
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        except InteligenciaApiError as exc:
            toast_error(exc)
            return

        st.subheader(resultado.indicador_nome or f"Indicador #{resultado.id_indicador}")
        if resultado.safra_nome:
            st.caption(f"Safra: {resultado.safra_nome}")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Medicoes", resultado.total_medicoes)
        c2.metric("Media", _fmt_decimal(resultado.valor_medio))
        c3.metric("Minimo", _fmt_decimal(resultado.valor_minimo))
        c4.metric("Maximo", _fmt_decimal(resultado.valor_maximo))
        c5.metric("Soma", _fmt_decimal(resultado.valor_soma))


def _fmt_decimal(valor: Decimal | None) -> str:
    if valor is None:
        return "—"
    return f"{valor:.2f}"


def _render_clima_tab() -> None:
    """Fonte principal de dados: API Open-Meteo. Ve-se e sincroniza-se aqui."""
    st.caption(
        "Dados vindos de API externa (Open-Meteo). Outras fontes serao "
        "conectadas aqui no futuro."
    )
    latitude, longitude = clima.render_localizacao(key_prefix="inteligencia_clima")
    clima.render_clima_atual(latitude=latitude, longitude=longitude)

    try:
        safras = _listar_safras()
    except Exception:
        safras = []
    mapa_safra = {"Nenhuma": None}
    mapa_safra.update({_label_safra(s): s["id_safra"] for s in safras})

    col_safra, col_botao = st.columns([3, 1])
    with col_safra:
        safra_escolha = st.selectbox(
            "Associar a safra (opcional)", list(mapa_safra.keys()), key="clima_safra"
        )
    with col_botao:
        st.write("")
        sincronizar = st.button("Sincronizar", type="primary", use_container_width=True)

    if sincronizar:
        try:
            resultado = _client().sync_clima(
                ClimaSyncRequestSchema(
                    latitude=latitude,
                    longitude=longitude,
                    id_safra=mapa_safra[safra_escolha],
                    data_referencia=date.today(),
                )
            )
            toast_ok(f"{len(resultado.ids_medicao)} medicoes de clima registradas.")
            st.rerun()
        except InteligenciaApiError as exc:
            toast_error(exc)

    st.divider()
    clima.render_clima_trend()


def _render_metricas_proprias() -> None:
    """Secundario: cadastro manual de indicadores/medicoes, fora do foco principal."""
    st.caption(
        "Uso avancado: cadastre indicadores e medicoes manuais quando nao houver "
        "uma API conectada para o dado que voce precisa."
    )
    with st.expander("Indicadores"):
        _render_indicadores()
    with st.expander("Medicoes manuais"):
        _render_medicoes()
    with st.expander("Agregacao"):
        _render_agregacao()


require_login()

setup_page("Inteligencia", "Indicadores vindos de APIs conectadas, com espaco para metricas proprias.")

tab_clima, tab_proprias = st.tabs(["Clima", "Metricas proprias"])

with tab_clima:
    _render_clima_tab()

with tab_proprias:
    _render_metricas_proprias()
