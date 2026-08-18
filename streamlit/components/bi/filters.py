"""BI filter bar: selectbox with Todos + period chips + clear button."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from calendar import monthrange

import streamlit as st

_TODAS = "Todas"
_TODOS = "Todos"
PERIOD_CHIPS = ("30 dias", "90 dias", "12 meses", "Personalizado")
PERIOD_DAYS = {
    "30 dias": 30,
    "90 dias": 90,
    "12 meses": 365,
}
DEFAULT_PERIOD = "90 dias"


@dataclass(frozen=True)
class FilterSelection:
    safra: str | None
    product: str | None
    supplier: str | None
    cliente: str | None
    start: date | None
    end: date | None

    def in_period(self, day: date | None) -> bool:
        if self.start is None and self.end is None:
            return True
        if day is None:
            return False
        if self.start is not None and day < self.start:
            return False
        if self.end is not None and day > self.end:
            return False
        return True

    def previous_span(self) -> tuple[date | None, date | None]:
        if self.start is None or self.end is None:
            return None, None
        length = (self.end - self.start).days + 1
        prev_end = self.start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=length - 1)
        return prev_start, prev_end


def _reset_token(prefix: str) -> int:
    key = f"{prefix}_filtros_reset"
    if key not in st.session_state:
        st.session_state[key] = 0
    return int(st.session_state[key])


def _clear_filters(prefix: str) -> None:
    st.session_state[f"{prefix}_filtros_reset"] = _reset_token(prefix) + 1
    st.rerun()


def _choice(label: str, none_label: str, options: list[str], key: str) -> str | None:
    escolha = st.selectbox(label, [none_label, *options], key=key)
    return None if escolha == none_label else escolha


def _period_range(chip: str | None, custom) -> tuple[date | None, date | None]:
    if chip == "Personalizado":
        if isinstance(custom, (list, tuple)) and len(custom) == 2:
            inicio, fim = custom
            if inicio and fim:
                return inicio, fim
        if isinstance(custom, date):
            return custom, custom
        return None, None
    days = PERIOD_DAYS.get(chip or DEFAULT_PERIOD, 90)
    end = date.today()
    return end - timedelta(days=days - 1), end


def filter_widget_key(prefix: str, field: str) -> str:
    return f"{prefix}_{field}_{_reset_token(prefix)}"


def chart_select_key(prefix: str, name: str) -> str:
    return f"{prefix}_{name}_{_reset_token(prefix)}"


def _as_mapping(obj) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            return dict(to_dict())
        except Exception:
            pass
    try:
        return dict(obj)
    except Exception:
        data = {}
        for key in ("x", "y", "label", "legendgroup", "customdata"):
            if hasattr(obj, key):
                data[key] = getattr(obj, key)
        return data


def _selection_points(event) -> list:
    if event is None:
        return []
    selection = (
        event.get("selection")
        if isinstance(event, dict)
        else getattr(event, "selection", None)
    )
    if selection is None:
        return []
    points = (
        selection.get("points")
        if isinstance(selection, dict)
        else getattr(selection, "points", None)
    )
    return list(points or [])


def _scalar_label(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    elif not isinstance(value, (str, bytes, dict)) and hasattr(value, "__getitem__"):
        try:
            if len(value) > 0:
                value = value[0]
        except Exception:
            pass
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def _point_category(point, field: str = "x") -> str | None:
    data = _as_mapping(point)
    for key in (field, "hovertext", "legendgroup", "label", "x"):
        label = _scalar_label(data.get(key))
        if label is not None:
            return label
    return None


def _points_sig(points: list) -> str:
    return repr([_point_category(point) for point in points])


def apply_bar_click(
    *,
    prefix: str,
    field: str,
    chart_key: str,
    none_label: str = _TODOS,
    point_field: str = "x",
    allowed: list[str] | None = None,
) -> None:
    """Apply a product/supplier filter from a bar-chart click stored in session_state.

    Must run before the matching selectbox is instantiated. A second click on the
    same bar toggles the filter off. An empty selection right after a click is
    ignored so a chart redraw does not undo the filter.
    """
    event = st.session_state.get(chart_key)
    points = _selection_points(event)
    sig = _points_sig(points)
    applied_key = f"{chart_key}__sig"
    skip_empty_key = f"{chart_key}__skip_empty"
    if st.session_state.get(applied_key) == sig:
        return
    st.session_state[applied_key] = sig

    widget_key = filter_widget_key(prefix, field)
    stored_key = f"{chart_key}__clicked"
    if not points:
        if st.session_state.pop(skip_empty_key, False):
            return
        last = st.session_state.pop(stored_key, None)
        if last is not None and st.session_state.get(widget_key) == last:
            st.session_state[widget_key] = none_label
        return
    value = _point_category(points[0], point_field)
    if value is None:
        return
    if allowed is not None and value not in allowed:
        return
    current = st.session_state.get(widget_key)
    if current == value:
        st.session_state[widget_key] = none_label
        st.session_state.pop(stored_key, None)
        st.session_state.pop(skip_empty_key, None)
    else:
        st.session_state[widget_key] = value
        st.session_state[stored_key] = value
        st.session_state[skip_empty_key] = True


def _as_month_start(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    if isinstance(value, datetime):
        return date(value.year, value.month, 1)
    if isinstance(value, date):
        return date(value.year, value.month, 1)
    if isinstance(value, (int, float)):
        seconds = value / 1000.0 if value > 1e11 else float(value)
        try:
            dt = datetime.utcfromtimestamp(seconds)
        except (OSError, OverflowError, ValueError):
            return None
        return date(dt.year, dt.month, 1)
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    day_text = text.split("T")[0][:10]
    try:
        parsed = datetime.strptime(day_text, "%Y-%m-%d")
    except ValueError:
        return None
    return date(parsed.year, parsed.month, 1)


def _month_end(day: date) -> date:
    return date(day.year, day.month, monthrange(day.year, day.month)[1])


def apply_month_click(*, prefix: str, chart_key: str) -> None:
    """Zoom the period filter to the clicked month; second click restores the previous chip."""
    event = st.session_state.get(chart_key)
    points = _selection_points(event)
    sig = _points_sig(points)
    applied_key = f"{chart_key}__sig"
    skip_empty_key = f"{chart_key}__skip_empty"
    if st.session_state.get(applied_key) == sig:
        return
    st.session_state[applied_key] = sig

    periodo_key = filter_widget_key(prefix, "periodo")
    custom_key = filter_widget_key(prefix, "data_custom")
    stored_key = f"{chart_key}__clicked"
    prev_key = f"{chart_key}__prev_periodo"

    def _restore_period() -> None:
        st.session_state[periodo_key] = st.session_state.pop(prev_key, DEFAULT_PERIOD)
        st.session_state.pop(custom_key, None)
        st.session_state.pop(stored_key, None)

    if not points:
        if st.session_state.pop(skip_empty_key, False):
            return
        if st.session_state.get(stored_key) is not None:
            _restore_period()
        return

    data = _as_mapping(points[0])
    month_start = _as_month_start(data.get("x"))
    if month_start is None:
        return
    month_end = _month_end(month_start)
    month_id = month_start.isoformat()
    current_custom = st.session_state.get(custom_key)
    start_sel = end_sel = None
    if isinstance(current_custom, (list, tuple)) and len(current_custom) == 2:
        start_sel, end_sel = current_custom[0], current_custom[1]
        if isinstance(start_sel, datetime):
            start_sel = start_sel.date()
        if isinstance(end_sel, datetime):
            end_sel = end_sel.date()
    already = (
        st.session_state.get(periodo_key) == "Personalizado"
        and start_sel == month_start
        and end_sel == month_end
    )
    if already or st.session_state.get(stored_key) == month_id:
        _restore_period()
        st.session_state.pop(skip_empty_key, None)
        return
    current_periodo = st.session_state.get(periodo_key)
    if current_periodo and current_periodo != "Personalizado":
        st.session_state[prev_key] = current_periodo
    st.session_state[periodo_key] = "Personalizado"
    st.session_state[custom_key] = (month_start, month_end)
    st.session_state[stored_key] = month_id
    st.session_state[skip_empty_key] = True


def render_filter_bar(
    *,
    prefix: str,
    safra_options: list[str] | None,
    product_options: list[str] | None,
    supplier_options: list[str] | None = None,
    cliente_options: list[str] | None = None,
) -> FilterSelection:
    """Render a compact filter bar.

    If safra_options or product_options is None or empty, the corresponding selectbox
    is omitted (useful for dashboards that don't need those dimensions).
    """
    token = _reset_token(prefix)
    has_safra = bool(safra_options)
    has_product = bool(product_options)
    has_supplier = bool(supplier_options)
    has_cliente = bool(cliente_options)

    # decide column widths dynamically based on visible controls
    visible_fields = [has_safra, has_product, has_supplier, has_cliente]
    field_count = sum(1 for v in visible_fields if v)
    show_clear = field_count > 0
    # when there are visible fields, reserve a small column for the clear button
    if show_clear:
        widths = [3] * field_count + [1]
    else:
        widths = [1]
    cols = st.columns(widths)

    col_idx = 0
    if has_safra:
        with cols[col_idx]:
            safra = _choice(
                "Safra",
                _TODAS,
                safra_options or [],
                key=f"{prefix}_safra_{token}",
            )
        col_idx += 1
    else:
        safra = None

    if has_product:
        with cols[col_idx]:
            product = _choice(
                "Produto",
                _TODOS,
                product_options or [],
                key=f"{prefix}_produto_{token}",
            )
        col_idx += 1
    else:
        product = None

    if has_supplier:
        with cols[col_idx]:
            supplier = _choice(
                "Fornecedor",
                _TODOS,
                supplier_options or [],
                key=f"{prefix}_fornecedor_{token}",
            )
        col_idx += 1
    else:
        supplier = None

    if has_cliente:
        with cols[col_idx]:
            cliente = _choice(
                "Cliente",
                _TODOS,
                cliente_options or [],
                key=f"{prefix}_cliente_{token}",
            )
        col_idx += 1
    else:
        cliente = None

    # clear column is the last column
    clear_col = cols[-1] if show_clear else None

    if show_clear and clear_col is not None:
        with clear_col:
            st.caption("\u00a0")
            if st.button(
                "Limpar",
                use_container_width=True,
                icon=":material/filter_alt_off:",
                key=f"{prefix}_limpar_{token}",
                help="Volta os filtros para Todas/Todos e o periodo para 90 dias.",
            ):
                _clear_filters(prefix)

    # Period control always shown
    periodo_key = f"{prefix}_periodo_{token}"
    custom_key = f"{prefix}_data_custom_{token}"
    periodo = st.segmented_control(
        "Periodo",
        options=list(PERIOD_CHIPS),
        default=DEFAULT_PERIOD,
        required=True,
        key=periodo_key,
    )
    custom = None
    if periodo == "Personalizado":
        date_kwargs: dict = {"key": custom_key}
        if custom_key not in st.session_state:
            date_kwargs["value"] = ()
        custom = st.date_input("Intervalo", **date_kwargs)

    start, end = _period_range(periodo, custom)
    if start and end:
        st.caption(f"Periodo: {start.strftime('%d/%m/%Y')} – {end.strftime('%d/%m/%Y')}")
    else:
        st.caption("Periodo: todo o historico (sem intervalo selecionado).")
    return FilterSelection(
        safra=safra,
        product=product,
        supplier=supplier,
        cliente=cliente,
        start=start,
        end=end,
    )
