from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

from components.shared.screens import setup_page

setup_page("Logistica")
st.write("Pagina inicial do modulo Logistica.")
