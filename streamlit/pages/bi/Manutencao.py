"""BI — Dashboard de Manutenção.

Página que integra o componente de BI para manutenção (custos e perfil).
"""

from __future__ import annotations

from pathlib import Path
import sys

_STREAMLIT_ROOT = Path(__file__).resolve().parents[2]
if str(_STREAMLIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_STREAMLIT_ROOT))

from components.bi.manutencao_dashboard import render
from services.identity_client import require_login

require_login()
render()
