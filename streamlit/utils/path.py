"""Ensure the Streamlit app root is importable as ``components`` / ``services``."""

from __future__ import annotations

import sys
from pathlib import Path

_STREAMLIT_ROOT = Path(__file__).resolve().parents[1]


def ensure_streamlit_path() -> None:
    root = str(_STREAMLIT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
