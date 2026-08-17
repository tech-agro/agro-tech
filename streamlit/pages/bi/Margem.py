"""BI — Margem por safra."""

from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[2]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

from components.bi.margem_dashboard import render
from services.identity_client import require_login

require_login()
render()
