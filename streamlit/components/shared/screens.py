"""Standard Streamlit CRUD helpers for Agro Tech.

Canonical screen (same for every module):

    [ Filtrar .............. ]  [ Novo ]

    | col | col | col |
    |-----|-----|-----|
    | ... | ... | ... |   <- AgGrid

    0 de N linha(s) selecionada(s).   [ Ver ] [ Editar ] [ Excluir ]

    Novo    -> st.dialog (create form)
    Ver     -> st.dialog (detail)
    Editar  -> st.dialog (edit form)
    Excluir -> confirm + delete

Module navigation stays in the Streamlit sidebar. No extra menus/tabs for entities.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from components.shared.logo.widgets import apply_sidebar_logo


def setup_page(title: str, caption: str | None = None) -> None:
    apply_sidebar_logo()
    st.title(title)
    if caption:
        st.caption(caption)


def filter_dataframe(df: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query or df.empty:
        return df
    needle = query.strip().lower()
    mask = (
        df.astype(str)
        .apply(lambda col: col.str.lower().str.contains(needle, na=False))
        .any(axis=1)
    )
    return df[mask]


def selected_rows(grid_response) -> list[dict]:
    rows = grid_response.get("selected_rows")
    if rows is None:
        return []
    if isinstance(rows, pd.DataFrame):
        return rows.to_dict("records")
    return list(rows)


def crud_toolbar(
    *,
    key: str,
    filter_placeholder: str = "Filtrar...",
    new_label: str = "Novo",
) -> tuple[str, bool]:
    """Filter input + Novo button. Returns (query, new_clicked)."""
    col_filter, col_new = st.columns([4, 1])
    with col_filter:
        query = st.text_input(
            "Filtrar",
            placeholder=filter_placeholder,
            label_visibility="collapsed",
            key=f"{key}_filter",
        )
    with col_new:
        new_clicked = st.button(
            new_label,
            type="primary",
            use_container_width=True,
            icon=":material/add:",
            key=f"{key}_new",
        )
    return query or "", new_clicked


def data_table(
    df: pd.DataFrame,
    *,
    key: str,
    height: int = 360,
    page_size: int = 8,
) -> list[dict]:
    """AgGrid with checkbox selection. Pair with row_actions for the footer.

    Do not pass theme=\"streamlit\": that string theme stays light and breaks
    dark mode. Omitting theme lets recent streamlit-aggrid follow Streamlit.
    """
    if df.columns.empty:
        st.info("Nenhum registro para exibir.")
        return []

    builder = GridOptionsBuilder.from_dataframe(df)
    builder.configure_selection("single", use_checkbox=True)
    builder.configure_pagination(
        enabled=True,
        paginationAutoPageSize=False,
        paginationPageSize=page_size,
    )
    builder.configure_default_column(resizable=True, filter=True, sortable=True)
    grid = AgGrid(
        df,
        gridOptions=builder.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        height=height,
        key=f"{key}_grid",
        reload_data=True,
    )
    return selected_rows(grid)


def row_actions(
    *,
    key: str,
    selected_count: int = 0,
    total_count: int = 0,
    disabled: bool = False,
    show_edit: bool = True,
) -> str | None:
    """Compact footer: selection caption + Ver / Editar / Excluir."""

    clicked: str | None = None

    if show_edit:
        col_info, col_view, col_edit, col_delete = st.columns([4, 1, 1, 1])

        with col_info:
            st.caption(f"{selected_count} de {total_count} linha(s) selecionada(s).")

        with col_view:
            if st.button(
                "Ver",
                icon=":material/visibility:",
                use_container_width=True,
                disabled=disabled,
                key=f"{key}_view",
            ):
                clicked = "view"

        with col_edit:
            if st.button(
                "Editar",
                icon=":material/edit:",
                use_container_width=True,
                disabled=disabled,
                key=f"{key}_edit",
            ):
                clicked = "edit"

        with col_delete:
            if st.button(
                "Excluir",
                icon=":material/delete:",
                use_container_width=True,
                disabled=disabled,
                key=f"{key}_delete",
            ):
                clicked = "delete"

    else:
        col_info, col_view, col_delete = st.columns([5, 1, 1])

        with col_info:
            st.caption(f"{selected_count} de {total_count} linha(s) selecionada(s).")

        with col_view:
            if st.button(
                "Ver",
                icon=":material/visibility:",
                use_container_width=True,
                disabled=disabled,
                key=f"{key}_view",
            ):
                clicked = "view"

        with col_delete:
            if st.button(
                "Excluir",
                icon=":material/delete:",
                use_container_width=True,
                disabled=disabled,
                key=f"{key}_delete",
            ):
                clicked = "delete"

    return clicked

def toast_ok(message: str) -> None:
    st.toast(message)


def toast_error(exc: Exception) -> None:
    """Show a user-facing error. Prefer Portuguese `user_message` when present."""
    message = getattr(exc, "user_message", None) or getattr(exc, "message", None) or str(exc)
    st.toast(f"Erro: {message}")
