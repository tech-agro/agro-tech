"""BI dashboard for the stock module."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from app.estoque.enum import MovementType, StatusLote
from components.bi import charts
from components.bi.filters import apply_bar_click, chart_select_key, render_filter_bar
from components.bi.widgets import delta_label, download_csv, fmt_int, fmt_qty, single_unit, unit_label
from components.shared.screens import setup_page, toast_error
from services import producao_client as producao_api
from services.estoque_client import EstoqueApiError, EstoqueClient

_SAIDA_TYPES = {
    MovementType.SAIDA_VENDA.value,
    MovementType.SAIDA_ATIVIDADE.value,
}
_ENTRADA_TYPES = {
    MovementType.ENTRADA_COMPRA.value,
    MovementType.ENTRADA_COLHEITA.value,
}
_COVER_DAYS = 15
_EXPIRY_DAYS = 30
_EXPIRY_COLORS = {
    "Ate 7 dias": "#B3392B",
    "8 a 15 dias": "#C9861E",
    "16 a 30 dias": "#0E8C7D",
}


def _expiry_band(days: int) -> str:
    if days <= 7:
        return "Ate 7 dias"
    if days <= 15:
        return "8 a 15 dias"
    return "16 a 30 dias"


_STATUS_LABELS = {
    "EM_ANALISE": "Em analise",
    "LIBERADO": "Liberado",
    "BLOQUEADO": "Bloqueado",
}
_STATUS_OPTIONS = ["Bloqueado", "Em analise", "Liberado"]
_STATUS_COLORS = ["#B3392B", "#C9861E", "#0E8C7D"]


def _previous_span(start: date, end: date) -> tuple[date, date]:
    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    return prev_end - timedelta(days=length - 1), prev_end


def _saidas_by_product(df_mov: pd.DataFrame, start: date, end: date) -> dict[int, float]:
    if df_mov.empty:
        return {}
    recorte = df_mov[
        (df_mov["dia"] >= start)
        & (df_mov["dia"] <= end)
        & (df_mov["tipo"].isin(_SAIDA_TYPES))
    ]
    if recorte.empty:
        return {}
    grouped = recorte.groupby("id_produto")["quantidade"].sum()
    return {int(pid): float(qty) for pid, qty in grouped.items()}


def _stock_at(stock_now: dict[int, float], df_mov: pd.DataFrame, at: date) -> dict[int, float]:
    result = dict(stock_now)
    if df_mov.empty:
        return result
    after = df_mov[df_mov["dia"] > at]
    if after.empty:
        return result
    net = after.groupby("id_produto")["delta"].sum()
    for pid, net_after in net.items():
        key = int(pid)
        result[key] = result.get(key, 0.0) - float(net_after)
    return result


def _product_kpis(
    product_ids: set[int],
    stock_map: dict[int, float],
    saidas_map: dict[int, float],
    days: int,
    blocked_ids: set[int],
) -> tuple[list[float], set[int], list[dict]]:
    giro_values: list[float] = []
    critical_ids: set[int] = set(blocked_ids)
    giro_rows: list[dict] = []
    for pid in sorted(product_ids):
        qty = stock_map.get(pid, 0.0)
        saidas = saidas_map.get(pid, 0.0)
        giro = (saidas / qty) if qty > 0 else None
        daily_out = saidas / days if days else 0.0
        cover = (qty / daily_out) if daily_out > 0 else None
        if (qty == 0 and saidas > 0) or (cover is not None and cover < _COVER_DAYS):
            critical_ids.add(pid)
        giro_atual = giro if giro is not None else 0.0
        if qty > 0:
            giro_values.append(giro_atual)
        giro_rows.append({"id_produto": pid, "Giro": giro_atual})
    return giro_values, critical_ids, giro_rows


def _lotes_vencendo(
    lotes: list,
    as_of: date,
    id_produtos: set[int] | None,
    lote_ids_safra: set[int] | None,
) -> list:
    limite = as_of + timedelta(days=_EXPIRY_DAYS)
    vencendo = []
    for lote in lotes:
        validade = lote.validade
        if validade is None:
            continue
        if validade < as_of or validade > limite:
            continue
        if id_produtos is not None and lote.id_produto not in id_produtos:
            continue
        if lote_ids_safra is not None and lote.id_lote not in lote_ids_safra:
            continue
        vencendo.append(lote)
    return vencendo


def _client() -> EstoqueClient:
    return EstoqueClient()


def _as_date(value) -> date | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _qty(value) -> float:
    if value is None:
        return 0.0
    return float(value)


def _signed_qty(tipo: str, quantidade: float) -> float:
    if tipo in _ENTRADA_TYPES:
        return quantidade
    if tipo in _SAIDA_TYPES:
        return -quantidade
    return 0.0


def _safra_label(item: dict) -> str:
    return f"{item.get('nome', 'Safra')} ({item.get('ano', '')})"


def _load_safra_lot_ids(
    lotes: list,
) -> tuple[list[dict], dict[int, set[int]]]:
    try:
        safras = producao_api.listar("/safras")
        plantios = producao_api.listar("/plantios")
        ordens = producao_api.listar("/ordens-producao")
        colheitas = producao_api.listar("/colheitas")
    except Exception:
        st.warning("Nao foi possivel carregar as safras para o filtro.")
        return [], {}

    ordem_safra = {int(o["id_ordem"]): int(o["id_safra"]) for o in ordens}
    plantio_safra = {
        int(p["id_plantio"]): ordem_safra.get(int(p["id_ordem"]))
        for p in plantios
        if int(p["id_ordem"]) in ordem_safra
    }
    colheita_safra = {
        int(c["id_colheita"]): plantio_safra.get(int(c["id_plantio"]))
        for c in colheitas
        if plantio_safra.get(int(c["id_plantio"])) is not None
    }

    lots_by_safra: dict[int, set[int]] = {}
    for lote in lotes:
        if lote.id_colheita is None:
            continue
        id_safra = colheita_safra.get(int(lote.id_colheita))
        if id_safra is None:
            continue
        lots_by_safra.setdefault(id_safra, set()).add(int(lote.id_lote))
    return safras, lots_by_safra


def _reconstruct_daily_stock(
    current_qty: float,
    movements: pd.DataFrame,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Rebuild daily on-hand qty from the current snapshot and later movements."""
    if movements.empty or "dia" not in movements.columns:
        rows = [
            {"Data": start + timedelta(days=offset), "Quantidade": max(current_qty, 0.0)}
            for offset in range((end - start).days + 1)
        ]
        return pd.DataFrame(rows)

    after = movements[movements["dia"] > end]
    net_after = float(after["delta"].sum()) if not after.empty else 0.0
    stock_at_end = current_qty - net_after

    in_period = movements[(movements["dia"] >= start) & (movements["dia"] <= end)]
    daily_net = (
        in_period.groupby("dia", as_index=False)["delta"].sum()
        if not in_period.empty
        else pd.DataFrame(columns=["dia", "delta"])
    )
    net_by_day = {row.dia: float(row.delta) for row in daily_net.itertuples(index=False)}

    rows = []
    running = stock_at_end - sum(net_by_day.get(day, 0.0) for day in net_by_day)
    cursor = start
    while cursor <= end:
        running += net_by_day.get(cursor, 0.0)
        rows.append({"Data": cursor, "Quantidade": max(running, 0.0)})
        cursor += timedelta(days=1)
    return pd.DataFrame(rows)


def render() -> None:
    setup_page("Estoque", "Indicadores de estoque e abastecimento")

    client = _client()
    try:
        produtos = client.list_produto_options()
        lotes = client.list_lotes(limit=1000)
        localizacoes = client.list_localizacao_lotes()
        saldos = client.list_all_saldos()
        movimentacoes = client.list_all_movimentacoes()
    except EstoqueApiError as exc:
        toast_error(exc)
        st.stop()

    safras, lots_by_safra = _load_safra_lot_ids(lotes)
    product_options = [p.nome for p in produtos]
    giro_key = chart_select_key("bi_estoque", "giro_produto")
    saldo_key = chart_select_key("bi_estoque", "saldo_produto")
    lotes_key = chart_select_key("bi_estoque", "lotes_vencimento")
    apply_bar_click(
        prefix="bi_estoque",
        field="produto",
        chart_key=giro_key,
        allowed=product_options,
    )
    apply_bar_click(
        prefix="bi_estoque",
        field="produto",
        chart_key=saldo_key,
        allowed=product_options,
    )
    apply_bar_click(
        prefix="bi_estoque",
        field="produto",
        chart_key=lotes_key,
        point_field="customdata",
        allowed=product_options,
    )
    filtros = render_filter_bar(
        prefix="bi_estoque",
        safra_options=[_safra_label(s) for s in safras],
        product_options=product_options,
    )

    id_produtos: set[int] | None = None
    if filtros.product:
        id_produtos = {p.id_produto for p in produtos if p.nome == filtros.product}

    lote_ids_safra: set[int] | None = None
    if filtros.safra:
        lote_ids_safra = set()
        for safra in safras:
            if _safra_label(safra) == filtros.safra:
                lote_ids_safra |= lots_by_safra.get(int(safra["id_safra"]), set())

    start = filtros.start
    end = filtros.end or date.today()
    if start is None:
        start = end - timedelta(days=89)

    lotes_by_id = {lote.id_lote: lote for lote in lotes}
    unit_by_product = {
        int(p.id_produto): unit_label(p.unidade_sigla) for p in produtos
    }

    loc_rows = []
    for loc in localizacoes:
        lote = lotes_by_id.get(loc.id_lote)
        if lote is None:
            continue
        if id_produtos is not None and lote.id_produto not in id_produtos:
            continue
        if lote_ids_safra is not None and loc.id_lote not in lote_ids_safra:
            continue
        loc_rows.append(
            {
                "id_lote": loc.id_lote,
                "id_produto": lote.id_produto,
                "produto": lote.produto_nome or loc.produto_nome or f"#{lote.id_produto}",
                "codigo": loc.codigo_lote,
                "quantidade": _qty(loc.quantidade_atual),
                "unidade": unit_by_product.get(int(lote.id_produto)),
                "status": lote.status.value if lote.status else None,
            }
        )
    df_loc = pd.DataFrame(loc_rows)

    if df_loc.empty:
        estoque_total = sum(
            _qty(s.quantidade_atual)
            for s in saldos
            if id_produtos is None or s.id_produto in id_produtos
        ) if lote_ids_safra is None else 0.0
        qty_by_product = (
            pd.DataFrame(
                [
                    {
                        "id_produto": s.id_produto,
                        "produto": s.produto_nome or f"#{s.id_produto}",
                        "quantidade": _qty(s.quantidade_atual),
                    }
                    for s in saldos
                    if id_produtos is None or s.id_produto in id_produtos
                ]
            )
            .groupby(["id_produto", "produto"], as_index=False)["quantidade"]
            .sum()
            if lote_ids_safra is None
            else pd.DataFrame(columns=["id_produto", "produto", "quantidade"])
        )
    else:
        estoque_total = float(df_loc["quantidade"].sum())
        qty_by_product = (
            df_loc.groupby(["id_produto", "produto"], as_index=False)["quantidade"].sum()
        )

    mov_rows = []
    for mov in movimentacoes:
        dia = _as_date(mov.data_movimentacao)
        if dia is None:
            continue
        if id_produtos is not None and mov.id_produto not in id_produtos:
            continue
        if lote_ids_safra is not None:
            if mov.id_lote is None or mov.id_lote not in lote_ids_safra:
                continue
        quantidade = _qty(mov.quantidade)
        mov_rows.append(
            {
                "dia": dia,
                "id_produto": mov.id_produto,
                "produto": mov.produto_nome or f"#{mov.id_produto}",
                "tipo": mov.tipo_movimentacao,
                "quantidade": quantidade,
                "delta": _signed_qty(mov.tipo_movimentacao, quantidade),
            }
        )
    df_mov = pd.DataFrame(mov_rows)
    df_evolucao = _reconstruct_daily_stock(estoque_total, df_mov, start, end)
    days = max((end - start).days + 1, 1)
    prev_start, prev_end = _previous_span(start, end)
    stock_map = {
        int(row.id_produto): float(row.quantidade)
        for row in qty_by_product.itertuples(index=False)
    } if not qty_by_product.empty else {}
    saidas_map = _saidas_by_product(df_mov, start, end)
    saidas_prev = _saidas_by_product(df_mov, prev_start, prev_end)
    stock_prev = _stock_at(stock_map, df_mov, prev_end)
    nomes = {
        **{int(p.id_produto): p.nome for p in produtos},
        **(
            {int(row.id_produto): row.produto for row in qty_by_product.itertuples(index=False)}
            if not qty_by_product.empty
            else {}
        ),
        **{pid: f"#{pid}" for pid in saidas_map},
    }
    product_ids = set(stock_map) | set(saidas_map)
    if id_produtos is not None:
        product_ids = {pid for pid in product_ids if pid in id_produtos}
    product_ids_prev = set(stock_prev) | set(saidas_prev)
    if id_produtos is not None:
        product_ids_prev = {pid for pid in product_ids_prev if pid in id_produtos}

    blocked_ids: set[int] = set()
    if not df_loc.empty:
        blocked = df_loc[df_loc["status"].isin({StatusLote.BLOQUEADO.value, StatusLote.EM_ANALISE.value})]
        blocked_ids = {int(pid) for pid in blocked["id_produto"].tolist()}

    giro_values, critical_ids, giro_raw = _product_kpis(
        product_ids, stock_map, saidas_map, days, blocked_ids
    )
    giro_prev_values, critical_prev, _ = _product_kpis(
        product_ids_prev, stock_prev, saidas_prev, days, blocked_ids
    )
    giro_rows = [
        {"Produto": nomes.get(row["id_produto"], f"#{row['id_produto']}"), "Giro": row["Giro"]}
        for row in giro_raw
    ]

    units_in_stock = {
        unit_by_product.get(int(row.id_produto))
        for row in qty_by_product.itertuples(index=False)
        if float(row.quantidade) > 0
    } if not qty_by_product.empty else set()
    estoque_unidade = single_unit(units_in_stock)
    n_produtos = (
        int((qty_by_product["quantidade"] > 0).sum())
        if not qty_by_product.empty
        else 0
    )
    n_produtos_prev = sum(1 for qty in stock_prev.values() if qty > 0)
    estoque_prev_total = sum(max(qty, 0.0) for qty in stock_prev.values())

    vencendo_filtrados = _lotes_vencendo(lotes, end, id_produtos, lote_ids_safra)
    vencendo_prev = _lotes_vencendo(lotes, prev_end, id_produtos, lote_ids_safra)

    giro_mediana = float(pd.Series(giro_values).median()) if giro_values else None
    giro_mediana_prev = (
        float(pd.Series(giro_prev_values).median()) if giro_prev_values else None
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    if filtros.product:
        unidade = None
        if id_produtos:
            unidade = single_unit({unit_by_product.get(pid) for pid in id_produtos})
        unidade = unidade or estoque_unidade
        col_m1.metric(
            "Estoque total",
            f"{fmt_qty(estoque_total)} {unidade}" if unidade else fmt_qty(estoque_total),
            delta=delta_label(estoque_total, estoque_prev_total, formatter=fmt_qty),
            help=(
                "Saldo atual do produto filtrado, na unidade cadastrada. "
                "Delta em relacao ao estoque no fim do periodo anterior."
            ),
        )
    else:
        col_m1.metric(
            "Produtos em estoque",
            str(n_produtos),
            delta=delta_label(n_produtos, n_produtos_prev, formatter=fmt_int),
            help=(
                "Produtos distintos com saldo no recorte. "
                "Nao soma kg, L e sc no mesmo total: filtre um produto para ver o estoque."
            ),
        )
    col_m2.metric(
        "Mediana do giro",
        fmt_qty(giro_mediana) if giro_mediana is not None else "—",
        delta=delta_label(giro_mediana, giro_mediana_prev, formatter=fmt_qty),
        help=(
            "Mediana do giro por produto (saidas do periodo / estoque atual). "
            "Nao e media ponderada pelo volume: um insumo de alto giro nao mascara os demais."
        ),
    )
    col_m3.metric(
        "Itens criticos",
        str(len(critical_ids)),
        delta=delta_label(len(critical_ids), len(critical_prev), formatter=fmt_int),
        delta_color="inverse",
        help=(
            f"Produto entra se: cobertura menor que {_COVER_DAYS} dias de saida "
            "(estoque / saida diaria do periodo), ruptura no periodo "
            "(estoque zerado com saida), ou lote bloqueado/em analise."
        ),
    )
    col_m4.metric(
        "Vencendo",
        str(len(vencendo_filtrados)),
        delta=delta_label(len(vencendo_filtrados), len(vencendo_prev), formatter=fmt_int),
        delta_color="inverse",
        help=f"Lotes com validade nos proximos {_EXPIRY_DAYS} dias a partir do fim do periodo.",
    )
    st.caption(
        "Itens criticos: cobertura < 15 dias de saida, ruptura no periodo "
        "ou lote bloqueado/em analise."
    )

    col_giro, col_lotes = st.columns(2)
    with col_giro:
        st.subheader("Giro por produto")
        df_giro = pd.DataFrame(giro_rows)
        log_y = False
        if not df_giro.empty:
            df_giro = df_giro[df_giro["Giro"] > 0].sort_values("Giro", ascending=False)
            giros = df_giro["Giro"]
            if len(giros) >= 2 and giros.max() / max(float(giros.min()), 1e-9) >= 8:
                log_y = True
        charts.bar_chart(
            df_giro,
            x="Produto",
            y="Giro",
            y_title="Giro (escala log)" if log_y else "Giro",
            x_title=None,
            log_y=log_y,
            select_key=giro_key,
        )
    with col_lotes:
        st.subheader("Lotes proximos do vencimento")
        qty_lote = (
            df_loc.groupby("id_lote", as_index=False)["quantidade"].sum()
            if not df_loc.empty
            else pd.DataFrame(columns=["id_lote", "quantidade"])
        )
        qty_lote_map = {
            int(row.id_lote): float(row.quantidade)
            for row in qty_lote.itertuples(index=False)
        } if not qty_lote.empty else {}
        expiry_rows = []
        for lote in vencendo_filtrados:
            validade = lote.validade
            if validade is None:
                continue
            lote_ref = lotes_by_id.get(lote.id_lote)
            produto_nome = (
                lote.produto_nome
                or (lote_ref.produto_nome if lote_ref is not None else None)
                or f"#{lote.id_produto}"
            )
            dias = max((validade - end).days, 0)
            expiry_rows.append(
                {
                    "Lote": lote.codigo_lote,
                    "Dias para vencer": dias,
                    "Quantidade": qty_lote_map.get(
                        lote.id_lote, _qty(lote.quantidade_inicial)
                    ),
                    "Produto": produto_nome,
                    "Faixa": _expiry_band(dias),
                }
            )
        df_expiry = (
            pd.DataFrame(expiry_rows).sort_values("Dias para vencer")
            if expiry_rows
            else pd.DataFrame()
        )
        if not df_expiry.empty:
            df_expiry["Lote"] = pd.Categorical(
                df_expiry["Lote"],
                categories=df_expiry["Lote"].tolist(),
                ordered=True,
            )
        charts.bar_chart(
            df_expiry,
            x="Lote",
            y="Quantidade",
            color="Faixa" if not df_expiry.empty else None,
            color_map=_EXPIRY_COLORS,
            y_title="Quantidade em risco",
            x_title=None,
            hover_data=["Produto", "Dias para vencer"],
            select_key=lotes_key,
        )

    if filtros.product:
        st.subheader("Evolucao do estoque")
        charts.line_chart(
            df_evolucao,
            x="Data",
            y="Quantidade",
            y_title="Quantidade",
            x_title=None,
        )
    else:
        st.subheader("Saldo por produto")
        df_saldo = (
            qty_by_product.rename(columns={"produto": "Produto", "quantidade": "Quantidade"})
            .sort_values("Quantidade", ascending=False)
            if not qty_by_product.empty
            else pd.DataFrame()
        )
        charts.bar_chart(
            df_saldo,
            x="Produto",
            y="Quantidade",
            y_title="Quantidade",
            x_title=None,
            select_key=saldo_key,
        )
        st.caption(
            "Sem produto filtrado, o saldo atual substitui a evolucao agregada "
            "(unidades diferentes nao devem ser somadas no mesmo eixo)."
        )

    st.subheader("Detalhamento")
    if df_loc.empty:
        st.info("Nenhum lote com saldo no recorte selecionado.")
        return

    detalhe_rows = []
    export_rows = []
    for row in df_loc.itertuples(index=False):
        lote = lotes_by_id.get(int(row.id_lote))
        validade = lote.validade if lote is not None else None
        status_label = _STATUS_LABELS.get(row.status or "", row.status or "")
        unidade = getattr(row, "unidade", None) or ""
        detalhe_rows.append(
            {
                "Lote": row.codigo,
                "Produto": row.produto,
                "Quantidade": fmt_qty(float(row.quantidade)),
                "Unidade": unidade,
                "Status": [status_label] if status_label else [],
                "Validade": validade.strftime("%d/%m/%Y") if validade else "",
            }
        )
        export_rows.append(
            {
                "Lote": row.codigo,
                "Produto": row.produto,
                "Quantidade": float(row.quantidade),
                "Unidade": unidade,
                "Status": status_label,
                "Validade": validade.strftime("%d/%m/%Y") if validade else "",
            }
        )
    st.dataframe(
        pd.DataFrame(detalhe_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.MultiselectColumn(
                "Status",
                options=_STATUS_OPTIONS,
                color=_STATUS_COLORS,
                disabled=True,
            ),
        },
    )
    download_csv(
        pd.DataFrame(export_rows),
        filename="estoque-detalhamento.csv",
        key="bi_estoque_csv",
    )
