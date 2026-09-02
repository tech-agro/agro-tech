"""Altair (Vega-Lite) chart helpers for BI dashboards.

Native to Streamlit — no extra chart library required — and automatically
themed from `.streamlit/config.toml` (`chartCategoricalColors`,
`chartSequentialColors`), so every dashboard shares one visual language in
both light and dark mode.

Click-to-filter contract: when `select_key` is given, the resolved click is
written to `st.session_state[select_key]` as
`{"selection": {"points": [{"x": ..., "legendgroup": ..., <field>: ...}]}}`,
matching the shape `components.bi.filters.apply_bar_click` /
`apply_month_click` already expect (kept field-name compatible with the
previous Plotly implementation on purpose, so the filter bar needed no
changes).
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from components.shared.charts import is_dark_theme
from components.shared.palette import CATEGORICAL

_TEAL = CATEGORICAL[0]


def _empty(message: str) -> None:
    st.info(message)


def _axis_kind(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "T"
    if pd.api.types.is_numeric_dtype(series):
        return "Q"
    return "N"


def _domain_order(df: pd.DataFrame, col: str, category_orders: dict[str, list[str]] | None) -> list:
    if category_orders and col in category_orders:
        return list(category_orders[col])
    seen: list = []
    for value in df[col]:
        if value not in seen:
            seen.append(value)
    return seen


def _color_encoding(
    df: pd.DataFrame,
    color: str | None,
    color_map: dict[str, str] | None,
    category_orders: dict[str, list[str]] | None,
):
    if color is None:
        return None
    if color_map:
        domain = list(color_map.keys())
        rng = list(color_map.values())
        scale = alt.Scale(domain=domain, range=rng)
    else:
        scale = alt.Scale(domain=_domain_order(df, color, category_orders))
    return alt.Color(f"{color}:N", title=None, scale=scale, legend=alt.Legend(orient="top"))


def _apply_click_selection(
    event,
    *,
    select_key: str,
    x_field: str,
    color_field: str | None,
) -> None:
    """Normalize a Vega-Lite selection event into the legacy point-dict shape."""
    raw_points: list[dict] = []
    if event is not None:
        selection = event.get("selection") if isinstance(event, dict) else getattr(event, "selection", None)
        selection = selection or {}
        raw_points = list(selection.get("points") or [])

    points = []
    for point in raw_points:
        point = dict(point)
        if x_field in point:
            point.setdefault("x", point[x_field])
        if color_field and color_field in point:
            point.setdefault("legendgroup", point[color_field])
        points.append(point)

    st.session_state[select_key] = {"selection": {"points": points}}


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

    if log_y:
        # A log scale is undefined at/below zero — Vega-Lite silently drops
        # every bar (renders nothing) if any y-value is <= 0.
        dropped = int((df[y] <= 0).sum())
        df = df[df[y] > 0]
        if df.empty:
            _empty("Sem valores positivos para exibir em escala log.")
            return
        if dropped:
            st.caption(f"{dropped} item(ns) com valor zero omitido(s) da escala log.")

    x_kind = _axis_kind(df[x])
    x_enc_kwargs: dict = {"title": x_title or x}
    if x_kind == "N":
        x_enc_kwargs["sort"] = _domain_order(df, x, category_orders)
        x_enc_kwargs["axis"] = alt.Axis(
            labelAngle=-40, grid=False, labelOverlap="greedy", labelLimit=140
        )
    else:
        x_enc_kwargs["axis"] = alt.Axis(grid=False)

    y_scale = alt.Scale(type="log") if log_y else alt.Undefined
    color_enc = _color_encoding(df, color, color_map, category_orders)

    tooltip = [alt.Tooltip(f"{x}:{x_kind}", title=x_title or x)]
    tooltip.append(alt.Tooltip(f"{y}:Q", title=y_title or y, format=",.2f"))
    if color:
        tooltip.append(alt.Tooltip(f"{color}:N", title=color))
    for field in hover_data or []:
        tooltip.append(alt.Tooltip(f"{field}:N", title=field))

    # mark_bar always anchors to the y=0 baseline, which is undefined on a
    # log scale (every bar silently renders at zero height). Dots have no
    # baseline to break, so use them instead whenever log_y is requested.
    base = (
        alt.Chart(df).mark_point(size=140, filled=True, opacity=0.9)
        if log_y
        else alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    )

    encode_kwargs: dict = {
        "x": alt.X(f"{x}:{x_kind}", **x_enc_kwargs),
        "y": alt.Y(f"{y}:Q", title=y_title or y, scale=y_scale, axis=alt.Axis(gridDash=[2, 3])),
        "tooltip": tooltip,
    }
    if color_enc is not None:
        encode_kwargs["color"] = color_enc
        if barmode == "group":
            encode_kwargs["xOffset"] = alt.XOffset(f"{color}:N", sort=_domain_order(df, color, category_orders))
    else:
        encode_kwargs["color"] = alt.value(_TEAL)

    chart = base.encode(**encode_kwargs).properties(height=height)
    if title:
        chart = chart.properties(title=title)

    kwargs: dict = {"height": height}
    if select_key:
        sel = alt.selection_point(name="points", fields=[x], on="click", empty=False, clear="dblclick")
        chart = chart.add_params(sel).encode(
            opacity=alt.condition(sel, alt.value(1.0), alt.value(0.55)),
        )
        event = st.altair_chart(chart, on_select="rerun", selection_mode=["points"], **kwargs)
        _apply_click_selection(event, select_key=select_key, x_field=x, color_field=color)
    else:
        st.altair_chart(chart, **kwargs)


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

    x_kind = _axis_kind(df[x])
    x_axis = alt.Axis(grid=False, title=x_title) if x_title is not None else alt.Axis(grid=False, title=None)
    x_enc_kwargs: dict = {"axis": x_axis}
    if x_kind == "N":
        x_enc_kwargs["sort"] = _domain_order(df, x, None)

    color_enc = _color_encoding(df, color, None, None)

    tooltip = [
        alt.Tooltip(f"{x}:{x_kind}", title=x_title or x),
        alt.Tooltip(f"{y}:Q", title=y_title or y, format=",.2f"),
    ]
    if color:
        tooltip.append(alt.Tooltip(f"{color}:N", title=color))

    base = alt.Chart(df).mark_line(point=alt.OverlayMarkDef(size=55), strokeWidth=2.5)
    encode_kwargs: dict = {
        "x": alt.X(f"{x}:{x_kind}", **x_enc_kwargs),
        "y": alt.Y(f"{y}:Q", title=y_title or y, axis=alt.Axis(gridDash=[2, 3])),
        "tooltip": tooltip,
    }
    if color_enc is not None:
        encode_kwargs["color"] = color_enc
    else:
        base = base.encode(color=alt.value(_TEAL))

    chart = base.encode(**encode_kwargs).properties(height=height)

    kwargs: dict = {"height": height}
    if select_key:
        sel = alt.selection_point(name="points", fields=[x], on="click", empty=False, clear="dblclick", nearest=True)
        chart = chart.add_params(sel).encode(
            size=alt.condition(sel, alt.value(4.0), alt.value(2.5)),
        )
        event = st.altair_chart(chart, on_select="rerun", selection_mode=["points"], **kwargs)
        _apply_click_selection(event, select_key=select_key, x_field=x, color_field=color)
    else:
        st.altair_chart(chart, **kwargs)


def _padded_domain(values: pd.Series, *, pad_frac: float = 0.18, min_pad: float = 0.0) -> list[float]:
    lo = float(values.min())
    hi = float(values.max())
    span = hi - lo
    pad = max(span * pad_frac, min_pad)
    if pad <= 0:
        pad = max(abs(hi) * pad_frac, min_pad, 1.0)
    return [lo - pad, hi + pad]


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

    color_enc = _color_encoding(df, color, None, None)
    tooltip = []
    if hover_name:
        tooltip.append(alt.Tooltip(f"{hover_name}:N", title=hover_name))
    tooltip += [
        alt.Tooltip(f"{x}:Q", title=x_title or x, format=",.2f"),
        alt.Tooltip(f"{y}:Q", title=y_title or y, format=",.2f"),
    ]
    if color:
        tooltip.append(alt.Tooltip(f"{color}:N", title=color))
    if size:
        tooltip.append(alt.Tooltip(f"{size}:Q", title=size, format=",.2f"))
    for field in hover_data or []:
        tooltip.append(alt.Tooltip(f"{field}:N", title=field))

    base = alt.Chart(df).mark_circle(opacity=0.75, stroke="white", strokeWidth=0.8)
    encode_kwargs: dict = {
        "x": alt.X(
            f"{x}:Q",
            title=x_title or x,
            scale=alt.Scale(domain=_padded_domain(df[x], pad_frac=0.18, min_pad=0.8)),
            axis=alt.Axis(grid=False),
        ),
        "y": alt.Y(
            f"{y}:Q",
            title=y_title or y,
            scale=alt.Scale(domain=_padded_domain(df[y], pad_frac=0.18, min_pad=0.0)),
            axis=alt.Axis(gridDash=[2, 3]),
        ),
        "tooltip": tooltip,
    }
    if size:
        encode_kwargs["size"] = alt.Size(
            f"{size}:Q",
            title=size,
            scale=alt.Scale(range=[sizemin * 6, size_max * 12]),
            legend=None,
        )
    if color_enc is not None:
        encode_kwargs["color"] = color_enc
    else:
        base = base.encode(color=alt.value(_TEAL))

    chart = base.encode(**encode_kwargs).properties(height=height)

    kwargs: dict = {"height": height}
    if select_key:
        fields = [color] if color else [x]
        sel = alt.selection_point(name="points", fields=fields, on="click", empty=False, clear="dblclick", nearest=True)
        chart = chart.add_params(sel).encode(
            opacity=alt.condition(sel, alt.value(1.0), alt.value(0.45)),
        )
        event = st.altair_chart(chart, on_select="rerun", selection_mode=["points"], **kwargs)
        _apply_click_selection(event, select_key=select_key, x_field=x, color_field=color)
    else:
        st.altair_chart(chart, **kwargs)


def donut_chart(
    df: pd.DataFrame,
    *,
    category: str,
    value: str,
    title: str | None = None,
    color_map: dict[str, str] | None = None,
    height: int = 280,
) -> None:
    """Donut chart — replacement for ad-hoc Plotly pies (e.g. preventiva x corretiva)."""
    if df.empty:
        _empty("Sem dados para exibir.")
        return

    scale = (
        alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))
        if color_map
        else alt.Scale(range=list(CATEGORICAL))
    )
    total = float(df[value].sum()) or 1.0
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=height * 0.22, outerRadius=height * 0.42, stroke="white", strokeWidth=1.5)
        .encode(
            theta=alt.Theta(f"{value}:Q"),
            color=alt.Color(f"{category}:N", title=None, scale=scale, legend=alt.Legend(orient="top")),
            tooltip=[
                alt.Tooltip(f"{category}:N", title="Categoria"),
                alt.Tooltip(f"{value}:Q", title=value, format=",.2f"),
            ],
        )
        .properties(height=height)
    )
    labels = (
        alt.Chart(df)
        .transform_calculate(pct=f"datum.{value} / {total}")
        .mark_text(radius=height * 0.34, fontSize=12, fontWeight="bold")
        .encode(
            theta=alt.Theta(f"{value}:Q", stack=True),
            text=alt.Text("pct:Q", format=".0%"),
            color=alt.value("white"),
        )
    )
    if title:
        chart = chart.properties(title=title)
    st.altair_chart(chart + labels, height=height)


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
        return f"rgba(36,92,83,{alpha})"
    red, green, blue = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    return f"rgba({red},{green},{blue},{alpha})"


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
        h = usable * (max(weight, 0.0) / total)
        ys.append(min(max(cursor - h / 2, 0.02), 0.98))
        cursor -= h + gap
    return ys, [usable * (max(w, 0.0) / total) for w in weights]


def _wrap_sankey_label(name: str, width: int = 24) -> str:
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
    return "\n".join(lines) or name


def _bezier_ribbon(x0: float, y0top: float, y0bot: float, x1: float, y1top: float, y1bot: float, n: int = 24) -> pd.DataFrame:
    """Sample points for a smooth S-curve flow ribbon between two columns."""
    rows = []
    cx0 = x0 + (x1 - x0) * 0.5
    cx1 = cx0
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3 * x0 + 3 * mt**2 * t * cx0 + 3 * mt * t**2 * cx1 + t**3 * x1
        y_top = mt**3 * y0top + 3 * mt**2 * t * y0top + 3 * mt * t**2 * y1top + t**3 * y1top
        y_bot = mt**3 * y0bot + 3 * mt**2 * t * y0bot + 3 * mt * t**2 * y1bot + t**3 * y1bot
        rows.append({"x": x, "y_top": y_top, "y_bot": y_bot, "order": i})
    return pd.DataFrame(rows)


def sankey_chart(
    df: pd.DataFrame,
    *,
    source: str,
    target: str,
    value: str,
    height: int = 420,
) -> None:
    """Flow diagram (origem -> destino) as layered Altair ribbons + node bars.

    A faithful, dependency-free stand-in for Plotly's Sankey trace: node
    stacking/weights use the same math as before, links are smooth bezier
    ribbons whose thickness encodes value.
    """
    if df.empty:
        _empty("Sem dados para exibir.")
        return

    sources = df[source].astype(str).tolist()
    targets = df[target].astype(str).tolist()
    values = df[value].astype(float).tolist()
    source_labels = list(dict.fromkeys(sources))
    target_labels = list(dict.fromkeys(targets))
    source_index = {name: idx for idx, name in enumerate(source_labels)}
    target_index = {name: idx for idx, name in enumerate(target_labels)}

    palette = list(CATEGORICAL) * 3
    source_colors = _column_colors(len(source_labels), palette, start=0)
    target_colors = _column_colors(len(target_labels), palette, start=len(source_labels) + 1)

    source_weights = [sum(v for n, v in zip(sources, values) if n == label) for label in source_labels]
    target_weights = [sum(v for n, v in zip(targets, values) if n == label) for label in target_labels]
    source_ys, source_heights = _sankey_stack_y(source_weights)
    target_ys, target_heights = _sankey_stack_y(target_weights)

    # Links: smooth ribbon per (source, target) pair, stacked within each node's band.
    source_cursor = [y + h / 2 for y, h in zip(source_ys, source_heights)]
    target_cursor = [y + h / 2 for y, h in zip(target_ys, target_heights)]
    ribbons: list[pd.DataFrame] = []
    for i, (s_name, t_name, v) in enumerate(zip(sources, targets, values)):
        si, ti = source_index[s_name], target_index[t_name]
        s_total = source_weights[si] or 1.0
        t_total = target_weights[ti] or 1.0
        s_band = source_heights[si] * (v / s_total)
        t_band = target_heights[ti] * (v / t_total)
        y0_top = source_cursor[si]
        y0_bot = y0_top - s_band
        source_cursor[si] = y0_bot
        y1_top = target_cursor[ti]
        y1_bot = y1_top - t_band
        target_cursor[ti] = y1_bot
        ribbon = _bezier_ribbon(0.04, y0_top, y0_bot, 0.96, y1_top, y1_bot)
        ribbon["link_id"] = i
        ribbon["color"] = _to_rgba(source_colors[si], alpha=0.4)
        ribbon["label"] = f"{s_name} → {t_name}: R$ {v:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")
        ribbons.append(ribbon)

    # One independent mark_area layer per link (rather than a single chart
    # grouped by `detail`) — avoids relying on Vega-Lite's detail/order
    # faceting for overlapping bands, which does not reliably draw every
    # group in all renderers.
    ribbon_layers = [
        alt.Chart(ribbon)
        .mark_area(interpolate="linear", opacity=0.55, color=ribbon["color"].iloc[0])
        .encode(
            x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, 1]), sort=None),
            y=alt.Y("y_bot:Q", axis=None, scale=alt.Scale(domain=[0, 1]), title=None),
            y2="y_top:Q",
        )
        for ribbon in ribbons
    ]
    ribbon_layer = alt.layer(*ribbon_layers)

    def _node_frame(labels: list[str], ys: list[float], heights: list[float], colors: list[str], x0: float, x1: float) -> pd.DataFrame:
        # `ys` holds each node's vertical CENTER (see `_sankey_stack_y`), so the
        # rect spans center ± half its height — not `ys` .. `ys + h`.
        return pd.DataFrame(
            {
                "label": labels,
                "y0": [y - h / 2 for y, h in zip(ys, heights)],
                "y1": [y + h / 2 for y, h in zip(ys, heights)],
                "color": colors,
                "x0": x0,
                "x1": x1,
            }
        )

    nodes_df = pd.concat(
        [
            _node_frame(source_labels, source_ys, source_heights, source_colors, 0.0, 0.04),
            _node_frame(target_labels, target_ys, target_heights, target_colors, 0.96, 1.0),
        ],
        ignore_index=True,
    )
    node_layer = (
        alt.Chart(nodes_df)
        .mark_rect()
        .encode(
            x=alt.X("x0:Q", axis=None, scale=alt.Scale(domain=[0, 1])),
            x2="x1:Q",
            y=alt.Y("y0:Q", axis=None, scale=alt.Scale(domain=[0, 1]), title=None),
            y2="y1:Q",
            color=alt.Color("color:N", scale=None, legend=None),
            tooltip=[alt.Tooltip("label:N", title="Nó")],
        )
    )

    label_color = "#E8EEF2" if is_dark_theme() else "#1A1A1A"

    def _label_frame(labels: list[str], ys: list[float], heights: list[float], x: float) -> pd.DataFrame:
        # `ys` is already each node's vertical center — label sits there directly.
        return pd.DataFrame(
            {
                "label": [_wrap_sankey_label(n) for n in labels],
                "y": list(ys),
                "x": x,
            }
        )

    def _label_layer(frame: pd.DataFrame, align: str) -> alt.Chart:
        return (
            alt.Chart(frame)
            .mark_text(fontSize=12, color=label_color, align=align)
            .encode(
                x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[0, 1])),
                y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[0, 1]), title=None),
                text="label:N",
            )
        )

    source_labels_df = _label_frame(source_labels, source_ys, source_heights, -0.015)
    target_labels_df = _label_frame(target_labels, target_ys, target_heights, 1.015)
    text_layer = _label_layer(source_labels_df, "right") + _label_layer(target_labels_df, "left")

    chart_height = max(height, 64 * max(len(source_labels), len(target_labels), 1) + 96)
    chart = (
        (ribbon_layer + node_layer + text_layer)
        .properties(height=chart_height)
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False, domain=False)
    )
    st.altair_chart(chart, height=chart_height)
