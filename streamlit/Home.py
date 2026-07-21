from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parent
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

import streamlit as st

st.set_page_config(page_title="Agro Tech", page_icon="🌱", layout="wide")
st.title("Agro Tech")
st.caption("Estrutura inicial")
st.write("Use o menu lateral para navegar entre os modulos.")
