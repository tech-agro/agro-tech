from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import pandas as pd
import streamlit as st

from app.producao.enum import (
    StatusAtividadeAgricola,
    StatusOperacaoAgricola,
    StatusOrdemProducao,
    StatusPlanejamentoSafra,
    StatusPlantio,
    StatusSafra,
)
from components.shared.screens import setup_page
from services import producao_client as producao_api
from services.identity_client import require_login

require_login()

setup_page(
    "Producao",
    "Ciclo produtivo: safra -> talhao -> planejamento -> ordem -> plantio -> operacoes/atividades -> colheita.",
)


# ----------------------------------------------------------------------
# Helpers genericos: listagem cacheada, selectbox por nome, tabela e acoes
# ----------------------------------------------------------------------
@st.cache_data(ttl=15)
def _listar(caminho: str, **filtros) -> list[dict]:
    filtros = {chave: valor for chave, valor in filtros.items() if valor not in (None, 0, "")}
    return producao_api.listar(caminho, filtros or None)


def _invalidar_cache() -> None:
    _listar.clear()


def _selecionar(label: str, registros: list[dict], rotulo_fn, chave_id: str, key: str, ajuda: str | None = None):
    """Selectbox por nome que devolve o id do registro escolhido (ou None)."""
    if not registros:
        st.caption(f"Nenhum(a) {label.lower()} cadastrado(a) ainda.")
        return None
    mapa = {rotulo_fn(r): r[chave_id] for r in registros}
    escolha = st.selectbox(label, list(mapa.keys()), key=key, help=ajuda)
    return mapa.get(escolha)


def _humanize(col: str) -> str:
    return col.replace("_", " ").strip().capitalize()


def _tabela(dados: list[dict]) -> None:
    """Generic table renderer for the many raw-dict listings in this page.

    No per-entity schema is known here, so formatting is inferred from the
    project's naming convention: `id_*`/`id` columns are integer ids,
    `dt_*`/`data_*` columns are dates, and other numeric columns get
    thousands separators — instead of a plain, unformatted grid.
    """
    if not dados:
        st.caption("Nenhum registro encontrado.")
        return

    df = pd.DataFrame(dados)
    column_config: dict = {}
    for col in df.columns:
        if col == "id" or col.startswith("id_"):
            column_config[col] = st.column_config.NumberColumn(
                _humanize(col), format="%d", pinned=(col == df.columns[0])
            )
        elif col.startswith("dt_") or col.startswith("data_"):
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().any():
                df[col] = parsed
                column_config[col] = st.column_config.DatetimeColumn(
                    _humanize(col), format="DD/MM/YYYY HH:mm"
                )
        elif pd.api.types.is_numeric_dtype(df[col]):
            column_config[col] = st.column_config.NumberColumn(_humanize(col), format="localized")

    st.dataframe(df, hide_index=True, column_config=column_config)


def _excluir(rotulo: str, caminho_base: str, id_valor: int | None, key: str) -> None:
    if id_valor is None:
        return
    if st.button(f"Excluir {rotulo} selecionado(a)", key=f"del_btn_{key}"):
        try:
            producao_api.remover(f"{caminho_base}/{id_valor}")
            _invalidar_cache()
            st.success(f"{rotulo} removido(a).")
            st.rerun()
        except RuntimeError as exc:
            st.error(str(exc))


def _acoes(caminho_base: str, id_valor: int | None, acoes: list[tuple[str, str]], key: str) -> None:
    """Botoes de operacao nomeada (iniciar/aprovar/concluir/cancelar/...) em vez de um selectbox de status cru."""
    if id_valor is None or not acoes:
        return
    colunas = st.columns(len(acoes))
    for coluna, (verbo, rotulo_botao) in zip(colunas, acoes):
        with coluna:
            if st.button(rotulo_botao, key=f"acao_{key}_{verbo}"):
                try:
                    producao_api.acionar(f"{caminho_base}/{id_valor}/{verbo}")
                    _invalidar_cache()
                    st.success(f"{rotulo_botao}: feito.")
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))


def _combinar_data_hora(rotulo: str, key: str, obrigatorio: bool = False) -> datetime | None:
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input(f"{rotulo} - data", value=date.today() if obrigatorio else None, key=f"{key}_data")
    with col2:
        hora = st.time_input(f"{rotulo} - hora", value=time(0, 0), key=f"{key}_hora")
    if data is None:
        return None
    return datetime.combine(data, hora)


# ----------------------------------------------------------------------
# Contexto global: Safra ativa (filtra as abas abaixo)
# ----------------------------------------------------------------------
st.subheader("Safra ativa")
safras = _listar("/safras")
id_safra_ativa = _selecionar(
    "Selecione a safra em que voce esta trabalhando",
    safras,
    lambda r: f"{r['nome']} {r['ano']} [{r['status']}] (ID {r['id_safra']})",
    "id_safra",
    "ctx_safra",
    ajuda="Todas as listagens e formularios abaixo usam esta safra como contexto.",
)
with st.expander("+ Criar nova safra"):
    with st.form("form_safra"):
        nome_safra = st.text_input("Nome da safra")
        ano = st.number_input("Ano", min_value=2000, max_value=2100, step=1, value=2026)
        status_safra_novo = st.selectbox("Status inicial", [s.value for s in StatusSafra])
        dt_inicio = st.date_input("Data de inicio", value=None)
        dt_fim = st.date_input("Data de fim", value=None)
        if st.form_submit_button("Criar safra"):
            try:
                producao_api.criar(
                    "/safras",
                    {
                        "nome": nome_safra,
                        "ano": int(ano),
                        "status": status_safra_novo,
                        "dt_inicio": dt_inicio.isoformat() if dt_inicio else None,
                        "dt_fim": dt_fim.isoformat() if dt_fim else None,
                    },
                )
                _invalidar_cache()
                st.success("Safra criada.")
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))
if safras:
    _acoes("/safras", id_safra_ativa, [("iniciar", "Iniciar"), ("finalizar", "Finalizar"), ("cancelar", "Cancelar")], "safra")
    _excluir("safra", "/safras", id_safra_ativa, "safra")

# ----------------------------------------------------------------------
# Resumo da safra ativa
# ----------------------------------------------------------------------
if id_safra_ativa is not None:
    talhoes_safra = _listar("/talhoes", id_safra=id_safra_ativa)
    planejamentos_safra = _listar("/planejamentos-safra", id_safra=id_safra_ativa)
    ordens_safra = _listar("/ordens-producao", id_safra=id_safra_ativa)
    ids_ordens = {o["id_ordem"] for o in ordens_safra}
    plantios_safra = [p for p in _listar("/plantios") if p["id_ordem"] in ids_ordens]
    ids_plantios = {p["id_plantio"] for p in plantios_safra}
    colheitas_safra = [c for c in _listar("/colheitas") if c["id_plantio"] in ids_plantios]

    st.markdown("**Resumo da safra ativa**")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Talhoes", len(talhoes_safra))
    c2.metric("Planejamentos", len(planejamentos_safra))
    c3.metric("Ordens de producao", len(ordens_safra))
    c4.metric("Plantios", len(plantios_safra))
    c5.metric("Colheitas", len(colheitas_safra))
else:
    talhoes_safra, planejamentos_safra, ordens_safra, plantios_safra, colheitas_safra = [], [], [], [], []

st.divider()

aba_fazenda, aba_cultura, aba_planejamento, aba_producao, aba_operacoes, aba_monitoramento, aba_colheita = st.tabs(
    ["Fazendas e Talhoes", "Culturas", "Planejamento", "Ordens e Plantio", "Operacoes e Atividades", "Monitoramento", "Colheita"]
)

# ----------------------------------------------------------------------
# Fazendas e Talhoes (+ Solo)
# ----------------------------------------------------------------------
with aba_fazenda:
    st.subheader("Fazendas")
    with st.form("form_fazenda"):
        nome = st.text_input("Nome")
        localizacao = st.text_input("Localizacao", value="")
        if st.form_submit_button("Criar fazenda"):
            try:
                producao_api.criar("/fazendas", {"nome": nome, "localizacao": localizacao or None})
                _invalidar_cache()
                st.success("Fazenda criada.")
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))
    fazendas = _listar("/fazendas")
    _tabela(fazendas)
    id_fazenda_sel = _selecionar(
        "Fazenda", fazendas, lambda r: f"{r['nome']} (ID {r['id_fazenda']})", "id_fazenda", "sel_fazenda"
    )
    _excluir("fazenda", "/fazendas", id_fazenda_sel, "fazenda")

    st.divider()
    st.subheader("Talhoes (da safra ativa)")
    if id_safra_ativa is None:
        st.info("Selecione uma safra ativa acima para cadastrar talhoes.")
    else:
        with st.form("form_talhao"):
            id_fazenda_talhao = _selecionar(
                "Fazenda", fazendas, lambda r: f"{r['nome']} (ID {r['id_fazenda']})", "id_fazenda", "talhao_fazenda"
            )
            nome_talhao = st.text_input("Nome do talhao")
            area_hectares = st.number_input("Area (hectares)", min_value=0.0, step=0.1)
            if st.form_submit_button("Criar talhao"):
                try:
                    producao_api.criar(
                        "/talhoes",
                        {
                            "id_fazenda": id_fazenda_talhao,
                            "id_safra": id_safra_ativa,
                            "nome": nome_talhao,
                            "area_hectares": area_hectares,
                        },
                    )
                    _invalidar_cache()
                    st.success("Talhao criado.")
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
        _tabela(talhoes_safra)
        id_talhao_sel = _selecionar(
            "Talhao", talhoes_safra, lambda r: f"{r['nome']} - {r['area_hectares']} ha (ID {r['id_talhao']})", "id_talhao", "sel_talhao"
        )
        _excluir("talhao", "/talhoes", id_talhao_sel, "talhao")

        st.divider()
        st.subheader("Solo do talhao selecionado")
        if id_talhao_sel is not None:
            solo_atual = producao_api.obter(f"/talhoes/{id_talhao_sel}/solo")
            if solo_atual:
                st.json(solo_atual)
            with st.form("form_solo"):
                tipo_solo = st.text_input("Tipo de solo", value="")
                textura = st.text_input("Textura", value="")
                profundidade_cm = st.number_input("Profundidade (cm)", min_value=0.0, step=1.0, key="solo_profundidade")
                if st.form_submit_button("Registrar solo para este talhao"):
                    try:
                        producao_api.criar(
                            "/solos",
                            {
                                "id_talhao": id_talhao_sel,
                                "tipo_solo": tipo_solo or None,
                                "textura": textura or None,
                                "profundidade_cm": profundidade_cm or None,
                            },
                        )
                        _invalidar_cache()
                        st.success("Solo registrado.")
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))

# ----------------------------------------------------------------------
# Culturas (catalogo, sem vinculo com safra)
# ----------------------------------------------------------------------
with aba_cultura:
    st.subheader("Culturas")
    with st.form("form_cultura"):
        nome_cultura = st.text_input("Nome")
        nome_cientifico = st.text_input("Nome cientifico", value="")
        variedade = st.text_input("Variedade", value="")
        ciclo_dias = st.number_input("Ciclo (dias)", min_value=0, step=1)
        tipo_cultura = st.text_input("Tipo de cultura", value="")
        if st.form_submit_button("Criar cultura"):
            try:
                producao_api.criar(
                    "/culturas",
                    {
                        "nome": nome_cultura,
                        "nome_cientifico": nome_cientifico or None,
                        "variedade": variedade or None,
                        "ciclo_dias": int(ciclo_dias) or None,
                        "tipo_cultura": tipo_cultura or None,
                    },
                )
                _invalidar_cache()
                st.success("Cultura criada.")
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))
    culturas = _listar("/culturas")
    _tabela(culturas)
    id_cultura_sel = _selecionar(
        "Cultura", culturas, lambda r: f"{r['nome']} (ID {r['id_cultura']})", "id_cultura", "sel_cultura"
    )
    _excluir("cultura", "/culturas", id_cultura_sel, "cultura")

# ----------------------------------------------------------------------
# Planejamento de Safra
# ----------------------------------------------------------------------
with aba_planejamento:
    st.subheader("Planejamento de safra (da safra ativa)")
    if id_safra_ativa is None:
        st.info("Selecione uma safra ativa acima.")
    else:
        with st.form("form_planejamento"):
            id_talhao_plan = _selecionar(
                "Talhao", talhoes_safra, lambda r: f"{r['nome']} (ID {r['id_talhao']})", "id_talhao", "plan_talhao"
            )
            culturas_disp = _listar("/culturas")
            id_cultura_plan = _selecionar(
                "Cultura", culturas_disp, lambda r: f"{r['nome']} (ID {r['id_cultura']})", "id_cultura", "plan_cultura"
            )
            status_plan_novo = st.selectbox("Status inicial", [s.value for s in StatusPlanejamentoSafra])
            meta_produtividade = st.number_input("Meta de produtividade", min_value=0.0, step=0.1, key="plan_meta")
            area_planejada = st.number_input("Area planejada (hectares)", min_value=0.0, step=0.1, key="plan_area")
            dt_plantio_previsto = st.date_input("Data de plantio prevista", value=None, key="plan_dt_plantio")
            dt_colheita_previsto = st.date_input("Data de colheita prevista", value=None, key="plan_dt_colheita")
            if st.form_submit_button("Criar planejamento"):
                try:
                    producao_api.criar(
                        "/planejamentos-safra",
                        {
                            "id_safra": id_safra_ativa,
                            "id_talhao": id_talhao_plan,
                            "id_cultura": id_cultura_plan,
                            "status": status_plan_novo,
                            "meta_produtividade": meta_produtividade or None,
                            "area_planejada": area_planejada or None,
                            "dt_plantio_previsto": dt_plantio_previsto.isoformat() if dt_plantio_previsto else None,
                            "dt_colheita_previsto": dt_colheita_previsto.isoformat() if dt_colheita_previsto else None,
                        },
                    )
                    _invalidar_cache()
                    st.success("Planejamento criado.")
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
        _tabela(planejamentos_safra)
        id_planejamento_sel = _selecionar(
            "Planejamento",
            planejamentos_safra,
            lambda r: f"Planejamento #{r['id_planejamento']} - talhao {r['id_talhao']} / cultura {r['id_cultura']} [{r['status']}]",
            "id_planejamento",
            "sel_planejamento",
        )
        _acoes(
            "/planejamentos-safra",
            id_planejamento_sel,
            [("aprovar", "Aprovar"), ("iniciar-execucao", "Iniciar execucao"), ("concluir", "Concluir"), ("cancelar", "Cancelar")],
            "planejamento",
        )
        _excluir("planejamento de safra", "/planejamentos-safra", id_planejamento_sel, "planejamento")

# ----------------------------------------------------------------------
# Ordens de Producao e Plantio
# ----------------------------------------------------------------------
with aba_producao:
    st.subheader("Ordens de producao (da safra ativa)")
    if id_safra_ativa is None:
        st.info("Selecione uma safra ativa acima.")
    else:
        with st.form("form_ordem"):
            status_ordem_novo = st.selectbox("Status inicial", [s.value for s in StatusOrdemProducao])
            data_abertura = st.date_input("Data de abertura", value=date.today(), key="ordem_data_abertura")
            if st.form_submit_button("Abrir ordem de producao para a safra ativa"):
                try:
                    producao_api.criar(
                        "/ordens-producao",
                        {"id_safra": id_safra_ativa, "status": status_ordem_novo, "data_abertura": data_abertura.isoformat()},
                    )
                    _invalidar_cache()
                    st.success("Ordem de producao criada.")
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
        _tabela(ordens_safra)
        id_ordem_sel = _selecionar(
            "Ordem de producao", ordens_safra, lambda r: f"Ordem #{r['id_ordem']} [{r['status']}]", "id_ordem", "sel_ordem"
        )
        _acoes("/ordens-producao", id_ordem_sel, [("iniciar", "Iniciar"), ("concluir", "Concluir"), ("cancelar", "Cancelar")], "ordem")
        _excluir("ordem de producao", "/ordens-producao", id_ordem_sel, "ordem")

        st.divider()
        st.subheader("Plantio")
        if not ordens_safra or not planejamentos_safra:
            st.info("Crie ao menos uma ordem de producao e um planejamento de safra antes de registrar um plantio.")
        else:
            with st.form("form_plantio"):
                id_ordem_plantio = _selecionar(
                    "Ordem de producao", ordens_safra, lambda r: f"Ordem #{r['id_ordem']} [{r['status']}]", "id_ordem", "plantio_ordem"
                )
                id_planejamento_plantio = _selecionar(
                    "Planejamento",
                    planejamentos_safra,
                    lambda r: f"Planejamento #{r['id_planejamento']} - talhao {r['id_talhao']} / cultura {r['id_cultura']} [{r['status']}]",
                    "id_planejamento",
                    "plantio_planejamento",
                )
                planejamento_escolhido = next(
                    (p for p in planejamentos_safra if p["id_planejamento"] == id_planejamento_plantio), None
                )
                if planejamento_escolhido:
                    st.caption(
                        f"Talhao e cultura vem do planejamento escolhido: "
                        f"talhao {planejamento_escolhido['id_talhao']}, cultura {planejamento_escolhido['id_cultura']}."
                    )
                id_produto_plantio = None
                try:
                    from services.comercial_client import CommercialClient

                    _products = CommercialClient().list_products()
                except Exception:
                    _products = []
                if _products:
                    _pmap = {f"{p.nome} (#{p.id_produto})": p.id_produto for p in _products}
                    _pchoice = st.selectbox("Produto (semente/muda)", list(_pmap.keys()), key="plantio_produto_sel")
                    id_produto_plantio = _pmap[_pchoice]
                else:
                    id_produto_plantio = int(
                        st.number_input(
                            "ID do produto (semente/muda)",
                            min_value=1,
                            step=1,
                            key="plantio_id_produto",
                        )
                    )
                status_plantio_novo = st.selectbox("Status inicial", [s.value for s in StatusPlantio])
                dt_plantio = st.date_input("Data de plantio", value=date.today(), key="plantio_dt_plantio")
                if st.form_submit_button("Registrar plantio"):
                    try:
                        producao_api.criar(
                            "/plantios",
                            {
                                "id_ordem": id_ordem_plantio,
                                "id_talhao": planejamento_escolhido["id_talhao"] if planejamento_escolhido else None,
                                "id_produto": int(id_produto_plantio),
                                "id_cultura": planejamento_escolhido["id_cultura"] if planejamento_escolhido else None,
                                "id_planejamento": id_planejamento_plantio,
                                "status": status_plantio_novo,
                                "dt_plantio": dt_plantio.isoformat() if dt_plantio else None,
                            },
                        )
                        _invalidar_cache()
                        st.success("Plantio registrado.")
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
            _tabela(plantios_safra)
            id_plantio_sel = _selecionar(
                "Plantio", plantios_safra, lambda r: f"Plantio #{r['id_plantio']} - talhao {r['id_talhao']} [{r['status']}]", "id_plantio", "sel_plantio"
            )
            _acoes("/plantios", id_plantio_sel, [("iniciar", "Iniciar"), ("cancelar", "Cancelar")], "plantio")
            _excluir("plantio", "/plantios", id_plantio_sel, "plantio")

            if id_plantio_sel is not None:
                st.markdown("**Colher este plantio** (registra a colheita e encerra o plantio)")
                with st.form("form_colher_plantio"):
                    quantidade_colhida_pl = st.number_input("Quantidade colhida", min_value=0.0, step=0.1, key="colher_quantidade")
                    dt_inicio_colheita_pl = st.date_input("Data de inicio da colheita", value=date.today(), key="colher_dt_inicio")
                    dt_fim_colheita_pl = st.date_input("Data de fim da colheita", value=None, key="colher_dt_fim")
                    if st.form_submit_button("Colher"):
                        try:
                            colheita_criada = producao_api.acionar(
                                f"/plantios/{id_plantio_sel}/colher",
                                {
                                    "quantidade_colhida": quantidade_colhida_pl or None,
                                    "dt_inicio": dt_inicio_colheita_pl.isoformat() if dt_inicio_colheita_pl else None,
                                    "dt_fim": dt_fim_colheita_pl.isoformat() if dt_fim_colheita_pl else None,
                                },
                            )
                            _invalidar_cache()
                            st.success(f"Colheita #{colheita_criada['id_colheita']} registrada; plantio encerrado.")
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))

# ----------------------------------------------------------------------
# Operacoes e Atividades (+ funcionarios e detalhes de aplicacao)
# ----------------------------------------------------------------------
with aba_operacoes:
    st.subheader("Operacoes agricolas (da safra ativa)")
    if id_safra_ativa is None or not plantios_safra:
        st.info("Selecione uma safra ativa com plantios registrados.")
        operacoes_plantios = []
    else:
        with st.form("form_operacao"):
            id_plantio_op = _selecionar(
                "Plantio", plantios_safra, lambda r: f"Plantio #{r['id_plantio']} [{r['status']}]", "id_plantio", "op_plantio"
            )
            id_funcionario_op = st.number_input(
                "ID do funcionario responsavel (cadastrado no modulo de Identidade/RH)", min_value=1, step=1, key="op_id_funcionario"
            )
            status_op_novo = st.selectbox("Status inicial", [s.value for s in StatusOperacaoAgricola])
            tipo_operacao = st.text_input("Tipo de operacao", value="")
            descricao_op = st.text_area("Descricao", value="", key="op_descricao")
            dt_inicio_op = _combinar_data_hora("Inicio", "op_inicio")
            dt_fim_op = _combinar_data_hora("Fim", "op_fim")
            if st.form_submit_button("Registrar operacao"):
                try:
                    producao_api.criar(
                        "/operacoes-agricolas",
                        {
                            "id_plantio": id_plantio_op,
                            "id_funcionario": int(id_funcionario_op),
                            "status": status_op_novo,
                            "tipo_operacao": tipo_operacao or None,
                            "descricao": descricao_op or None,
                            "dt_inicio": dt_inicio_op.isoformat() if dt_inicio_op else None,
                            "dt_fim": dt_fim_op.isoformat() if dt_fim_op else None,
                        },
                    )
                    _invalidar_cache()
                    st.success("Operacao registrada.")
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
        ids_plantios_safra = {p["id_plantio"] for p in plantios_safra}
        operacoes_plantios = [o for o in _listar("/operacoes-agricolas") if o["id_plantio"] in ids_plantios_safra]
        _tabela(operacoes_plantios)
        id_operacao_sel = _selecionar(
            "Operacao", operacoes_plantios, lambda r: f"Operacao #{r['id_operacao']} - {r.get('tipo_operacao') or 's/tipo'} [{r['status']}]", "id_operacao", "sel_operacao"
        )
        _acoes("/operacoes-agricolas", id_operacao_sel, [("iniciar", "Iniciar"), ("concluir", "Concluir"), ("cancelar", "Cancelar")], "operacao")
        _excluir("operacao agricola", "/operacoes-agricolas", id_operacao_sel, "operacao")

    st.divider()
    st.subheader("Atividades agricolas")
    if not operacoes_plantios:
        st.info("Registre ao menos uma operacao agricola acima.")
        atividades_operacoes = []
    else:
        with st.form("form_atividade"):
            id_operacao_ativ = _selecionar(
                "Operacao", operacoes_plantios, lambda r: f"Operacao #{r['id_operacao']} [{r['status']}]", "id_operacao", "ativ_operacao"
            )
            status_ativ_novo = st.selectbox("Status inicial", [s.value for s in StatusAtividadeAgricola])
            descricao_ativ = st.text_area("Descricao", value="", key="ativ_descricao")
            dt_inicio_ativ = _combinar_data_hora("Inicio", "ativ_inicio")
            dt_fim_ativ = _combinar_data_hora("Fim", "ativ_fim")
            if st.form_submit_button("Registrar atividade"):
                try:
                    producao_api.criar(
                        "/atividades-agricolas",
                        {
                            "id_operacao": id_operacao_ativ,
                            "status": status_ativ_novo,
                            "descricao": descricao_ativ or None,
                            "dt_inicio": dt_inicio_ativ.isoformat() if dt_inicio_ativ else None,
                            "dt_fim": dt_fim_ativ.isoformat() if dt_fim_ativ else None,
                        },
                    )
                    _invalidar_cache()
                    st.success("Atividade registrada.")
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
        ids_operacoes = {o["id_operacao"] for o in operacoes_plantios}
        atividades_operacoes = [a for a in _listar("/atividades-agricolas") if a["id_operacao"] in ids_operacoes]
        _tabela(atividades_operacoes)
        id_atividade_sel = _selecionar(
            "Atividade", atividades_operacoes, lambda r: f"Atividade #{r['id_atividade']} [{r['status']}]", "id_atividade", "sel_atividade"
        )
        _acoes("/atividades-agricolas", id_atividade_sel, [("iniciar", "Iniciar"), ("concluir", "Concluir"), ("cancelar", "Cancelar")], "atividade")
        _excluir("atividade agricola", "/atividades-agricolas", id_atividade_sel, "atividade")

        if id_atividade_sel is not None:
            st.divider()
            st.subheader(f"Funcionarios e detalhes de aplicacao da atividade #{id_atividade_sel}")

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                id_funcionario_link = st.number_input(
                    "ID do funcionario (Identidade/RH)", min_value=1, step=1, key="func_id_funcionario"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("Vincular", key="func_btn_vincular"):
                    try:
                        producao_api.criar(f"/atividades-agricolas/{id_atividade_sel}/funcionarios/{int(id_funcionario_link)}", {})
                        st.success("Funcionario vinculado.")
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
            with col3:
                st.write("")
                st.write("")
                if st.button("Desvincular", key="func_btn_desvincular"):
                    try:
                        producao_api.remover(f"/atividades-agricolas/{id_atividade_sel}/funcionarios/{int(id_funcionario_link)}")
                        st.success("Funcionario desvinculado.")
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
            _tabela(producao_api.listar(f"/atividades-agricolas/{id_atividade_sel}/funcionarios"))

            aba_adub, aba_irrig, aba_pulv = st.tabs(["Adubacao", "Irrigacao", "Pulverizacao"])
            with aba_adub:
                registro_adubacao = producao_api.obter(f"/atividades-agricolas/{id_atividade_sel}/adubacao")
                if registro_adubacao:
                    st.json(registro_adubacao)
                with st.form("form_adubacao"):
                    id_insumo_adub = st.number_input("ID do insumo (Estoque)", min_value=1, step=1, key="adub_id_insumo")
                    tipo_adubacao = st.text_input("Tipo de adubacao", value="")
                    dose_hectare_adub = st.number_input("Dose por hectare", min_value=0.0, step=0.1, key="adub_dose")
                    metodo_aplicacao = st.text_input("Metodo de aplicacao", value="", key="adub_metodo")
                    if st.form_submit_button("Salvar adubacao"):
                        try:
                            producao_api.upsert(
                                f"/atividades-agricolas/{id_atividade_sel}/adubacao",
                                {
                                    "id_insumo": int(id_insumo_adub),
                                    "tipo_adubacao": tipo_adubacao or None,
                                    "dose_hectare": dose_hectare_adub or None,
                                    "metodo_aplicacao": metodo_aplicacao or None,
                                },
                            )
                            st.success("Adubacao salva.")
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))

            with aba_irrig:
                registro_irrigacao = producao_api.obter(f"/atividades-agricolas/{id_atividade_sel}/irrigacao")
                if registro_irrigacao:
                    st.json(registro_irrigacao)
                with st.form("form_irrigacao"):
                    lamina_agua = st.number_input("Lamina de agua", min_value=0.0, step=0.1, key="irrig_lamina")
                    metodo_irrigacao = st.text_input("Metodo de irrigacao", value="", key="irrig_metodo")
                    duracao_horas = st.number_input("Duracao (horas)", min_value=0.0, step=0.5, key="irrig_duracao")
                    if st.form_submit_button("Salvar irrigacao"):
                        try:
                            producao_api.upsert(
                                f"/atividades-agricolas/{id_atividade_sel}/irrigacao",
                                {
                                    "lamina_agua": lamina_agua or None,
                                    "metodo_irrigacao": metodo_irrigacao or None,
                                    "duracao_horas": duracao_horas or None,
                                },
                            )
                            st.success("Irrigacao salva.")
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))

            with aba_pulv:
                registro_pulverizacao = producao_api.obter(f"/atividades-agricolas/{id_atividade_sel}/pulverizacao")
                if registro_pulverizacao:
                    st.json(registro_pulverizacao)
                with st.form("form_pulverizacao"):
                    id_insumo_pulv = st.number_input("ID do insumo (Estoque)", min_value=1, step=1, key="pulv_id_insumo")
                    volume_calda = st.number_input("Volume de calda", min_value=0.0, step=0.1, key="pulv_volume")
                    vazao = st.number_input("Vazao", min_value=0.0, step=0.1, key="pulv_vazao")
                    if st.form_submit_button("Salvar pulverizacao"):
                        try:
                            producao_api.upsert(
                                f"/atividades-agricolas/{id_atividade_sel}/pulverizacao",
                                {"id_insumo": int(id_insumo_pulv), "volume_calda": volume_calda or None, "vazao": vazao or None},
                            )
                            st.success("Pulverizacao salva.")
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))

# ----------------------------------------------------------------------
# Monitoramento (clima, solo, safra)
# ----------------------------------------------------------------------
with aba_monitoramento:
    aba_clima_monit, aba_solo_monit, aba_fenologia_monit = st.tabs(
        ["Clima", "Solo", "Fenologia"]
    )

    with aba_clima_monit:
        st.subheader("Condicoes climaticas (da safra ativa)")
        if id_safra_ativa is None or not talhoes_safra:
            st.info("Selecione uma safra ativa com talhoes cadastrados.")
        else:
            with st.form("form_condicao_climatica"):
                id_talhao_clima = _selecionar(
                    "Talhao", talhoes_safra, lambda r: f"{r['nome']} (ID {r['id_talhao']})", "id_talhao", "clima_talhao"
                )
                dt_registro = _combinar_data_hora("Registro", "clima_registro", obrigatorio=True)

                st.caption("Essenciais")
                col_temp, col_umidade, col_precip = st.columns(3)
                with col_temp:
                    temperatura_min = st.number_input("Temperatura minima", step=0.1, key="clima_temp_min")
                    temperatura_max = st.number_input("Temperatura maxima", step=0.1, key="clima_temp_max")
                with col_umidade:
                    umidade_relativa = st.number_input("Umidade relativa (%)", min_value=0.0, max_value=100.0, step=0.1, key="clima_umidade")
                with col_precip:
                    precipitacao_mm = st.number_input("Precipitacao (mm)", min_value=0.0, step=0.1, key="clima_precipitacao")

                st.caption("Opcionais")
                col_vento1, col_vento2, col_radiacao = st.columns(3)
                with col_vento1:
                    velocidade_vento = st.number_input("Velocidade do vento", min_value=0.0, step=0.1, key="clima_vento")
                with col_vento2:
                    direcao_vento = st.text_input("Direcao do vento", value="", key="clima_direcao")
                with col_radiacao:
                    radiacao_solar = st.number_input("Radiacao solar", min_value=0.0, step=0.1, key="clima_radiacao")

                if st.form_submit_button("Registrar condicao climatica"):
                    try:
                        producao_api.criar(
                            "/condicoes-climaticas",
                            {
                                "id_talhao": id_talhao_clima,
                                "dt_registro": dt_registro.isoformat(),
                                "temperatura_min": temperatura_min or None,
                                "temperatura_max": temperatura_max or None,
                                "umidade_relativa": umidade_relativa or None,
                                "precipitacao_mm": precipitacao_mm or None,
                                "velocidade_vento": velocidade_vento or None,
                                "direcao_vento": direcao_vento or None,
                                "radiacao_solar": radiacao_solar or None,
                            },
                        )
                        _invalidar_cache()
                        st.success("Condicao climatica registrada.")
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
            ids_talhoes_safra = {t["id_talhao"] for t in talhoes_safra}
            condicoes = [c for c in _listar("/condicoes-climaticas") if c["id_talhao"] in ids_talhoes_safra]
            _tabela(condicoes)
            id_condicao_sel = _selecionar(
                "Condicao climatica", condicoes, lambda r: f"#{r['id_condicao']} - {r['dt_registro']}", "id_condicao", "sel_clima"
            )
            _excluir("condicao climatica", "/condicoes-climaticas", id_condicao_sel, "clima")

    with aba_solo_monit:
        st.subheader("Analises de solo")
        with st.form("form_analise_solo"):
            col_id, col_macro, col_micro = st.columns(3)
            with col_id:
                st.caption("Identificacao")
                id_solo_analise = st.number_input("ID do solo", min_value=1, step=1, key="analise_id_solo", help="Veja o ID em Fazendas e Talhoes > Solo do talhao selecionado.")
                id_funcionario_analise = st.number_input("ID do funcionario (Identidade/RH)", min_value=1, step=1, key="analise_id_funcionario")
                dt_coleta = st.date_input("Data de coleta", value=None, key="analise_dt_coleta")
                dt_resultado = st.date_input("Data de resultado", value=None, key="analise_dt_resultado")
            with col_macro:
                st.caption("Macronutrientes")
                ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1, key="analise_ph")
                materia_organica = st.number_input("Materia organica", min_value=0.0, step=0.1, key="analise_materia_organica")
                fosforo = st.number_input("Fosforo", min_value=0.0, step=0.1, key="analise_fosforo")
                potassio = st.number_input("Potassio", min_value=0.0, step=0.1, key="analise_potassio")
            with col_micro:
                st.caption("Demais parametros")
                calcio = st.number_input("Calcio", min_value=0.0, step=0.1, key="analise_calcio")
                magnesio = st.number_input("Magnesio", min_value=0.0, step=0.1, key="analise_magnesio")
                saturacao_bases = st.number_input("Saturacao de bases", min_value=0.0, step=0.1, key="analise_saturacao")
            observacao_analise = st.text_area("Observacao", value="", key="analise_observacao")
            if st.form_submit_button("Registrar analise de solo"):
                try:
                    producao_api.criar(
                        "/analises-solo",
                        {
                            "id_solo": int(id_solo_analise),
                            "id_safra": id_safra_ativa,
                            "id_funcionario": int(id_funcionario_analise),
                            "dt_coleta": dt_coleta.isoformat() if dt_coleta else None,
                            "dt_resultado": dt_resultado.isoformat() if dt_resultado else None,
                            "ph": ph or None,
                            "materia_organica": materia_organica or None,
                            "fosforo": fosforo or None,
                            "potassio": potassio or None,
                            "calcio": calcio or None,
                            "magnesio": magnesio or None,
                            "saturacao_bases": saturacao_bases or None,
                            "observacao": observacao_analise or None,
                        },
                    )
                    _invalidar_cache()
                    st.success("Analise de solo registrada.")
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
        analises = _listar("/analises-solo", id_safra=id_safra_ativa) if id_safra_ativa else []
        _tabela(analises)
        id_analise_sel = _selecionar("Analise de solo", analises, lambda r: f"#{r['id_analise']} - solo {r['id_solo']}", "id_analise", "sel_analise")
        _excluir("analise de solo", "/analises-solo", id_analise_sel, "analise")

    with aba_fenologia_monit:
        st.subheader("Monitoramento de safra (da safra ativa)")
        if id_safra_ativa is None or not talhoes_safra:
            st.info("Selecione uma safra ativa com talhoes cadastrados.")
            monitoramentos = []
        else:
            with st.form("form_monitoramento"):
                id_talhao_monit = _selecionar(
                    "Talhao", talhoes_safra, lambda r: f"{r['nome']} (ID {r['id_talhao']})", "id_talhao", "monit_talhao"
                )
                id_funcionario_monit = st.number_input("ID do funcionario (Identidade/RH)", min_value=1, step=1, key="monit_id_funcionario")
                dt_monitoramento = _combinar_data_hora("Monitoramento", "monit_dt", obrigatorio=True)
                estagio_fenologico = st.text_input("Estagio fenologico", value="", key="monit_estagio")
                observacao_monit = st.text_area("Observacao", value="", key="monit_observacao")
                if st.form_submit_button("Registrar monitoramento"):
                    try:
                        producao_api.criar(
                            "/monitoramentos-safra",
                            {
                                "id_safra": id_safra_ativa,
                                "id_talhao": id_talhao_monit,
                                "id_funcionario": int(id_funcionario_monit),
                                "dt_monitoramento": dt_monitoramento.isoformat(),
                                "estagio_fenologico": estagio_fenologico or None,
                                "observacao": observacao_monit or None,
                            },
                        )
                        _invalidar_cache()
                        st.success("Monitoramento registrado.")
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
            monitoramentos = _listar("/monitoramentos-safra", id_safra=id_safra_ativa)
            _tabela(monitoramentos)
            id_monitoramento_sel = _selecionar(
                "Monitoramento", monitoramentos, lambda r: f"#{r['id_monitoramento']} - {r['dt_monitoramento']}", "id_monitoramento", "sel_monitoramento"
            )
            _excluir("monitoramento de safra", "/monitoramentos-safra", id_monitoramento_sel, "monitoramento")

            if id_monitoramento_sel is not None:
                st.markdown(f"**Parametros do monitoramento #{id_monitoramento_sel}**")
                with st.form("form_parametro"):
                    nome_parametro = st.text_input("Nome do parametro", value="")
                    valor_parametro = st.number_input("Valor", step=0.1, key="param_valor")
                    unidade_parametro = st.text_input("Unidade", value="", key="param_unidade")
                    if st.form_submit_button("Adicionar parametro"):
                        try:
                            producao_api.criar(
                                f"/monitoramentos-safra/{id_monitoramento_sel}/parametros",
                                {"nome_parametro": nome_parametro, "valor": valor_parametro or None, "unidade": unidade_parametro or None},
                            )
                            st.success("Parametro adicionado.")
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))
                parametros = producao_api.listar(f"/monitoramentos-safra/{id_monitoramento_sel}/parametros")
                _tabela(parametros)
                id_parametro_sel = _selecionar(
                    "Parametro", parametros, lambda r: f"{r['nome_parametro']} = {r.get('valor')}", "id_parametro", "sel_parametro"
                )
                _excluir("parametro de monitoramento", "/parametros-monitoramento", id_parametro_sel, "parametro")

# ----------------------------------------------------------------------
# Colheita
# ----------------------------------------------------------------------
with aba_colheita:
    st.subheader("Colheitas (da safra ativa)")
    st.caption("Uma colheita nasce da acao \"Colher\" na aba Ordens e Plantio (isso ja encerra o plantio). Aqui voce acompanha e avanca o andamento de cada colheita ja aberta.")
    if id_safra_ativa is None or not plantios_safra:
        st.info("Selecione uma safra ativa com plantios registrados.")
    else:
        _tabela(colheitas_safra)
        id_colheita_sel = _selecionar(
            "Colheita", colheitas_safra, lambda r: f"Colheita #{r['id_colheita']} - plantio {r['id_plantio']} [{r['status']}]", "id_colheita", "sel_colheita"
        )
        _acoes("/colheitas", id_colheita_sel, [("iniciar", "Iniciar"), ("concluir", "Concluir"), ("cancelar", "Cancelar")], "colheita")
        _excluir("colheita", "/colheitas", id_colheita_sel, "colheita")
