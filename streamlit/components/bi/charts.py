"""Plotly helpers for BI dashboards."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.shared.charts import is_dark_theme

_TEAL = "#0E8C7D"
_CATEGORICAL = px.colors.qualitative.Set2


def _template() -> str:
    return "plotly_dark" if is_dark_theme() else "plotly_white"


def _empty(message: str) -> None:
    st.info(message)


def bar_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    title: str | None = None,
    color: str | None = None,
    color_map: dict[str, str] | None = None,
    category_orders: dict[str, list[str]] | None = None,
    hover_data: list[str] | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    log_y: bool = False,
    height: int = 320,
    select_key: str | None = None,
    barmode: str | None = None,
) -> None:
    if df.empty:
        _empty("Sem dados para exibir.")
        return

    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        color_discrete_map=color_map,
        category_orders=category_orders,
        hover_data=hover_data,
        title=title,
        template=_template(),
        height=height,
        log_y=log_y,
    )
    if color is None:
        fig.update_traces(marker_color=_TEAL)
    fig.update_layout(
        margin=dict(l=8, r=8, t=16 if title else 8, b=8),
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
        legend_title=None,
        showlegend=color is not None,
    )
    if barmode is not None:
        fig.update_layout(barmode=barmode)
    fig.update_xaxes(tickangle=-30)
    kwargs: dict = {
        "use_container_width": True,
        "config": {"displayModeBar": False},
    }
    if select_key:
        kwargs["key"] = select_key
        kwargs["on_select"] = "rerun"
        kwargs["selection_mode"] = "points"
    st.plotly_chart(fig, **kwargs)


def line_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    height: int = 320,
    select_key: str | None = None,
) -> None:
    if df.empty:
        _empty("Sem dados para exibir.")
        return

    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        markers=True,
        template=_template(),
        height=height,
    )
    if color is None:
        fig.update_traces(line_color=_TEAL)
    if select_key:
        fig.update_traces(marker=dict(size=11))
    fig.update_layout(
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis_title=x_title,
        yaxis_title=y_title or y,
        legend_title=None,
        showlegend=color is not None,
    )
    kwargs: dict = {
        "use_container_width": True,
        "config": {"displayModeBar": False},
    }
    if select_key:
        kwargs["key"] = select_key
        kwargs["on_select"] = "rerun"
        kwargs["selection_mode"] = "points"
    st.plotly_chart(fig, **kwargs)


def _padded_range(
    values: pd.Series,
    *,
    pad_frac: float = 0.18,
    min_pad: float = 0.0,
) -> tuple[float, float]:
    lo = float(values.min())
    hi = float(values.max())
    span = hi - lo
    pad = max(span * pad_frac, min_pad)
    if pad <= 0:
        pad = max(abs(hi) * pad_frac, min_pad, 1.0)
    return lo - pad, hi + pad


def scatter_chart(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: str | None = None,
    size: str | None = None,
    hover_name: str | None = None,
    hover_data: list[str] | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    size_max: int = 48,
    height: int = 320,
    select_key: str | None = None,
    sizemin: int = 12,
) -> None:
    if df.empty:
        _empty("Sem dados para exibir.")
        return

    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        size=size,
        hover_name=hover_name,
        hover_data=hover_data,
        color_discrete_sequence=_CATEGORICAL,
        template=_template(),
        height=height,
        size_max=size_max,
    )
    marker: dict = {"sizemin": sizemin}
    if color is None:
        marker["color"] = _TEAL
    fig.update_traces(marker=marker)
    x_min, x_max = _padded_range(df[x], pad_frac=0.18, min_pad=0.8)
    y_min, y_max = _padded_range(df[y], pad_frac=0.18, min_pad=0.0)
    fig.update_layout(
        margin=dict(l=16, r=16, t=8, b=16),
        xaxis_title=x_title or x,
        yaxis_title=y_title or y,
        legend_title=None,
        showlegend=color is not None,
    )
    fig.update_xaxes(range=[x_min, x_max])
    fig.update_yaxes(range=[y_min, y_max])
    kwargs: dict = {
        "use_container_width": True,
        "config": {"displayModeBar": False},
    }
    if select_key:
        kwargs["key"] = select_key
        kwargs["on_select"] = "rerun"
        kwargs["selection_mode"] = "points"
    st.plotly_chart(fig, **kwargs)


def _to_rgba(color: str, alpha: float = 0.35) -> str:
    text = color.strip()
    lowered = text.lower()
    if lowered.startswith("rgba("):
        return text
    if lowered.startswith("rgb("):
        inner = text[text.find("(") + 1 : text.rfind(")")]
        parts = [part.strip() for part in inner.split(",")]
        if len(parts) >= 3:
            return f"rgba({parts[0]},{parts[1]},{parts[2]},{alpha})"
        return text
    raw = text.lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) < 6:
        return f"rgba(14,140,125,{alpha})"
    red, green, blue = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    return f"rgba({red},{green},{blue},{alpha})"


def _sankey_palette() -> list[str]:
    seen: set[str] = set()
    colors: list[str] = []
    for color in (
        px.colors.qualitative.Set2
        + px.colors.qualitative.Dark2
        + px.colors.qualitative.Set1
        + px.colors.qualitative.Safe
    ):
        if color in seen:
            continue
        seen.add(color)
        colors.append(color)
    return colors


def _column_colors(count: int, palette: list[str], *, start: int = 0) -> list[str]:
    colors: list[str] = []
    idx = start
    size = len(palette)
    for _ in range(count):
        color = palette[idx % size]
        if colors and color == colors[-1]:
            idx += 1
            color = palette[idx % size]
        colors.append(color)
        idx += 1
    return colors


def _sankey_stack_y(
    weights: list[float],
    *,
    gap: float = 0.045,
    margin: float = 0.03,
) -> list[float]:
    n = len(weights)
    if n == 0:
        return []
    total = sum(max(w, 0.0) for w in weights) or 1.0
    usable = max(1.0 - 2 * margin - gap * max(n - 1, 0), 0.2)
    ys: list[float] = []
    cursor = 1.0 - margin
    for weight in weights:
        height = usable * (max(weight, 0.0) / total)
        ys.append(min(max(cursor - height / 2, 0.02), 0.98))
        cursor -= height + gap
    return ys


def _wrap_sankey_label(name: str, width: int = 22) -> str:
    if len(name) <= width:
        return name
    parts = name.split(" ")
    lines: list[str] = []
    current = ""
    for part in parts:
        trial = f"{current} {part}".strip()
        if current and len(trial) > width:
            lines.append(current)
            current = part
        else:
            current = trial
    if current:
        lines.append(current)
    return "<br>".join(lines) or name


def _sankey_side_labels(
    names: list[str],
    ys: list[float],
    *,
    side: str,
    color: str,
) -> list[dict]:
    left = side == "left"
    return [
        dict(
            x=0 if left else 1,
            y=y,
            xref="paper",
            yref="paper",
            text=_wrap_sankey_label(name),
            showarrow=False,
            xanchor="right" if left else "left",
            yanchor="middle",
            xshift=-14 if left else 14,
            font=dict(size=12, color=color),
            align="right" if left else "left",
        )
        for name, y in zip(names, ys)
    ]


def sankey_chart(
    df: pd.DataFrame,
    *,
    source: str,
    target: str,
    value: str,
    height: int = 420,
) -> None:
    if df.empty:
        _empty("Sem dados para exibir.")
        return

    sources = df[source].astype(str).tolist()
    targets = df[target].astype(str).tolist()
    values = df[value].astype(float).tolist()
    source_labels = list(dict.fromkeys(sources))
    target_labels = list(dict.fromkeys(targets))
    labels = source_labels + target_labels
    source_index = {name: idx for idx, name in enumerate(source_labels)}
    target_index = {
        name: idx + len(source_labels) for idx, name in enumerate(target_labels)
    }
    palette = _sankey_palette()
    source_colors = _column_colors(len(source_labels), palette, start=0)
    target_colors = _column_colors(
        len(target_labels),
        palette,
        start=len(source_labels) + 1,
    )
    if target_colors and source_colors and target_colors[0] == source_colors[-1]:
        target_colors = _column_colors(
            len(target_labels),
            palette,
            start=len(source_labels) + 2,
        )
    node_colors = source_colors + target_colors
    link_colors = [
        _to_rgba(source_colors[source_index[name]]) for name in sources
    ]
    source_weights = [
        sum(val for name, val in zip(sources, values) if name == label)
        for label in source_labels
    ]
    target_weights = [
        sum(val for name, val in zip(targets, values) if name == label)
        for label in target_labels
    ]
    source_ys = _sankey_stack_y(source_weights)
    target_ys = _sankey_stack_y(target_weights)
    n_nodes = max(len(source_labels), len(target_labels), 1)
    chart_height = max(height, 64 * n_nodes + 96)
    label_color = "#E8EEF2" if is_dark_theme() else "#1A1A1A"
    fig = go.Figure(
        go.Sankey(
            arrangement="fixed",
            textfont=dict(color="rgba(0,0,0,0)", size=1),
            node=dict(
                label=labels,
                color=node_colors,
                pad=28,
                thickness=18,
                line=dict(width=0),
                x=[0.02] * len(source_labels) + [0.98] * len(target_labels),
                y=source_ys + target_ys,
                hovertemplate="%{label}<extra></extra>",
            ),
            link=dict(
                source=[source_index[name] for name in sources],
                target=[target_index[name] for name in targets],
                value=values,
                color=link_colors,
                hovertemplate=(
                    "%{source.label} → %{target.label}"
                    "<br>Valor: R$ %{value:,.2f}<extra></extra>"
                ),
            ),
        )
    )
    fig.update_layout(
        template=_template(),
        height=chart_height,
        margin=dict(l=176, r=200, t=16, b=24),
        font=dict(size=12, color=label_color),
        annotations=(
            _sankey_side_labels(
                source_labels, source_ys, side="left", color=label_color
            )
            + _sankey_side_labels(
                target_labels, target_ys, side="right", color=label_color
            )
        ),
    )
    fig.update_traces(textfont=dict(color="rgba(0,0,0,0)", size=1))
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )
