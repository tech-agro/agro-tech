"""Inteligência financeira: KPIs, fluxo de caixa e vencimentos."""

from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

_TEAL_LIGHT, _TEAL_DARK = "#0E8C7D", "#2FA090"
_AMBER_LIGHT, _AMBER_DARK = "#C9861E", "#B3811F"
_CRITICAL = "#B3392B"
_WARNING = "#C1521F"
_GOOD = "#2E7D46"

_ABERTOS_PAGAR = {"ABERTA", "PARCIALMENTE_PAGA", "VENCIDA"}
_ABERTOS_RECEBER = {"ABERTA", "PARCIALMENTE_RECEBIDA", "VENCIDA"}

_BUCKET_ORDER = ["Vencidas", "Até 7 dias", "8–15 dias", "16–30 dias", "Mais de 30 dias"]


def _brl(valor) -> str:
    texto = f"{float(valor):,.2f}"
    return "R$ " + texto.replace(",", "§").replace(".", ",").replace("§", ".")


def _is_dark() -> bool:
    return st.context.theme.type == "dark" if hasattr(st, "context") and hasattr(st.context, "theme") else False


def _cores() -> tuple[str, str]:
    return (_TEAL_DARK, _AMBER_DARK) if _is_dark() else (_TEAL_LIGHT, _AMBER_LIGHT)


from components.bi.widgets import fmt_brl
from components.shared.palette import badge_column, badge_value


def render_kpis(contas_pagar: list, contas_receber: list) -> None:
    a_receber = sum(float(c.saldo) for c in contas_receber if c.status in _ABERTOS_RECEBER)
    a_pagar = sum(float(c.saldo) for c in contas_pagar if c.status in _ABERTOS_PAGAR)
    recebido = sum(float(c.valor_recebido) for c in contas_receber)
    pago = sum(float(c.valor) - float(c.saldo) for c in contas_pagar)
    saldo_projetado = a_receber - a_pagar

    with st.container(horizontal=True):
        st.metric("A receber (em aberto)", fmt_brl(a_receber), border=True)
        st.metric("A pagar (em aberto)", fmt_brl(a_pagar), border=True)
        st.metric(
            "Saldo projetado",
            fmt_brl(saldo_projetado),
            delta="Superávit" if saldo_projetado >= 0 else "Déficit",
            delta_color="normal" if saldo_projetado >= 0 else "inverse",
            help="A receber (em aberto) − A pagar (em aberto). Positivo é saudável.",
            border=True,
        )
        st.metric("Já recebido", fmt_brl(recebido), border=True)
        st.metric("Já pago", fmt_brl(pago), border=True)

def render_fluxo_chart(fluxo: list) -> None:
    teal, amber = _cores()
    linhas = []
    for f in fluxo:
        if f.data_movimento is None:
            continue
        if f.id_conta_receber is not None:
            linhas.append({"data": f.data_movimento, "tipo": "Entradas", "valor": float(f.valor)})
        elif f.id_conta_pagar is not None:
            linhas.append({"data": f.data_movimento, "tipo": "Saídas", "valor": -float(f.valor)})

    if not linhas:
        st.info("Sem movimentações de fluxo de caixa no período selecionado.")
        return

    df = pd.DataFrame(linhas).groupby(["data", "tipo"], as_index=False)["valor"].sum()

    chart = (
        alt.Chart(df)
        .mark_bar(size=14)
        .encode(
            x=alt.X("data:T", title=None),
            y=alt.Y("valor:Q", title="Valor (R$)"),
            color=alt.Color(
                "tipo:N",
                title=None,
                scale=alt.Scale(domain=["Entradas", "Saídas"], range=[teal, amber]),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("data:T", title="Data"),
                alt.Tooltip("tipo:N", title="Tipo"),
                alt.Tooltip("valor:Q", title="Valor", format=",.2f"),
            ],
        )
        .properties(height=280)
    )
    zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="gray", strokeWidth=1).encode(y="y:Q")
    st.altair_chart(chart + zero_rule)


def _bucket(vencimento: date | None, hoje: date) -> str | None:
    if vencimento is None:
        return None
    dias = (vencimento - hoje).days
    if dias < 0:
        return "Vencidas"
    if dias <= 7:
        return "Até 7 dias"
    if dias <= 15:
        return "8–15 dias"
    if dias <= 30:
        return "16–30 dias"
    return "Mais de 30 dias"


def render_aging_chart(contas_pagar: list, contas_receber: list) -> None:
    teal, amber = _cores()
    hoje = date.today()
    linhas = []
    for c in contas_pagar:
        if c.status not in _ABERTOS_PAGAR:
            continue
        b = _bucket(c.vencimento, hoje)
        if b:
            linhas.append({"bucket": b, "tipo": "A pagar", "valor": float(c.saldo)})
    for c in contas_receber:
        if c.status not in _ABERTOS_RECEBER:
            continue
        b = _bucket(c.vencimento, hoje)
        if b:
            linhas.append({"bucket": b, "tipo": "A receber", "valor": float(c.saldo)})

    if not linhas:
        st.info("Nenhuma conta em aberto com vencimento definido.")
        return

    df = pd.DataFrame(linhas).groupby(["bucket", "tipo"], as_index=False)["valor"].sum()

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("bucket:N", title=None, sort=_BUCKET_ORDER),
            y=alt.Y("valor:Q", title="Valor (R$)"),
            xOffset="tipo:N",
            color=alt.Color(
                "tipo:N",
                title=None,
                scale=alt.Scale(domain=["A receber", "A pagar"], range=[teal, amber]),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("bucket:N", title="Vencimento"),
                alt.Tooltip("tipo:N", title="Tipo"),
                alt.Tooltip("valor:Q", title="Valor", format=",.2f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(chart)

    vencidas = [l for l in linhas if l["bucket"] == "Vencidas"]
    if vencidas:
        total_vencido = sum(l["valor"] for l in vencidas)
        st.error(
            f"{_brl(total_vencido)} em contas já vencidas — priorize a regularização."
        )


_TIPO_TONE = {"A pagar": "orange", "A receber": "blue"}


def _humanize_origem(origem: str | None) -> str:
    if not origem:
        return "-"
    return " ".join(word.capitalize() for word in origem.replace("_", " ").split())


def render_criticas_table(contas_pagar: list, contas_receber: list) -> None:
    hoje = date.today()
    linhas = []
    for c in contas_pagar:
        if c.status in _ABERTOS_PAGAR and c.vencimento and c.vencimento < hoje:
            linhas.append(
                {
                    "Tipo": "A pagar",
                    "Origem": _humanize_origem(c.origem),
                    "Vencimento": c.vencimento,
                    "Dias em atraso": (hoje - c.vencimento).days,
                    "Saldo": float(c.saldo),
                }
            )
    for c in contas_receber:
        if c.status in _ABERTOS_RECEBER and c.vencimento and c.vencimento < hoje:
            linhas.append(
                {
                    "Tipo": "A receber",
                    "Origem": f"Venda #{c.id_venda}",
                    "Vencimento": c.vencimento,
                    "Dias em atraso": (hoje - c.vencimento).days,
                    "Saldo": float(c.saldo),
                }
            )

    if not linhas:
        st.success("Nenhuma conta vencida no momento.")
        return

    df = pd.DataFrame(linhas).sort_values("Dias em atraso", ascending=False)
    df["Saldo"] = df["Saldo"].astype(float)
    df["Tipo"] = df["Tipo"].apply(badge_value)
    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "Tipo": badge_column("Tipo", ["A pagar", "A receber"], _TIPO_TONE, width="small"),
            "Origem": st.column_config.TextColumn("Origem"),
            "Vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
            "Dias em atraso": st.column_config.ProgressColumn(
                "Dias em atraso", format="%d dias", min_value=0, max_value=60, color="red",
            ),
            "Saldo": st.column_config.NumberColumn("Saldo (R$)", format="localized"),
        },
    )
