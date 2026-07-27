"""Single source of truth for the Agro Tech root-crown mark geometry."""

from __future__ import annotations

# Aligned with .streamlit/config.toml
INK = "#245C53"   # hero mark (primary)
FLOW = "#2F8F83"  # hero animation accent

# Top-left ``st.logo`` — greens that stay visible on each surface
LOGO_SIDEBAR = "#D1E7E3"       # soft green on dark teal sidebar
LOGO_HEADER_LIGHT = "#245C53"  # primary green on light header (menu collapsed)
LOGO_HEADER_DARK = "#4DB6AC"   # accent green on dark header (menu collapsed)

MARK_VIEWBOX = "85 88 230 150"
ICON_VIEWBOX = "120 100 160 130"
WORDMARK_VIEWBOX = "85 88 460 150"
HERO_VIEWBOX = "0 0 400 300"

# (name, cx, cy, rx, ry)
NODULES = (
    ("Producao", 200, 150, 7.2, 6.4),
    ("Comercial", 170, 122, 5.0, 4.4),
    ("Compras", 138, 150, 5.1, 4.6),
    ("Estoque", 152, 186, 4.8, 5.2),
    ("Financeiro", 188, 206, 5.0, 4.5),
    ("Fitossanidade", 230, 188, 4.9, 5.3),
    ("Inteligencia", 248, 154, 5.1, 4.5),
    ("Logistica", 228, 118, 4.8, 5.1),
    ("Manutencao", 118, 188, 4.6, 5.0),
)

# (d, width, dash_len, delay)
PATHS = (
    ("M200 150 C178 148, 158 148, 138 150", 4.4, 75, 0.55),
    ("M200 150 C218 148, 234 150, 248 154", 4.4, 65, 0.60),
    ("M200 150 C188 136, 178 128, 170 122", 3.6, 55, 0.70),
    ("M200 150 C214 136, 222 126, 228 118", 3.6, 55, 0.75),
    ("M200 150 C194 170, 190 190, 188 206", 3.5, 70, 0.80),
    ("M138 150 C132 164, 140 176, 152 186", 3.2, 60, 1.05),
    ("M152 186 C140 192, 126 190, 118 188 C106 186, 98 196, 102 208", 2.4, 85, 1.30),
    ("M138 150 C120 152, 108 160, 104 172 C102 180, 96 186, 90 184", 2.2, 75, 1.25),
    ("M248 154 C246 168, 240 180, 230 188", 3.2, 55, 1.10),
    ("M230 188 C238 198, 248 204, 258 202 C266 200, 270 208, 266 214", 2.2, 70, 1.35),
    ("M170 122 C158 114, 148 108, 140 100 C134 94, 128 96, 126 102", 2.3, 65, 1.20),
    ("M228 118 C238 108, 246 100, 252 94 C256 90, 260 92, 258 98", 2.3, 60, 1.22),
    ("M188 206 C182 214, 176 220, 172 226 C170 230, 174 232, 178 230", 2.1, 50, 1.40),
    ("M248 154 C262 158, 272 162, 278 168 C282 172, 286 170, 284 164", 2.2, 55, 1.28),
)

# Compact collapsed-sidebar icon (subset + thicker strokes; matches prior asset).
ICON_PATHS = (
    ("M200 150 C178 148, 158 148, 138 150", 5.0),
    ("M200 150 C218 148, 234 150, 248 154", 5.0),
    ("M200 150 C188 136, 178 128, 170 122", 4.0),
    ("M200 150 C214 136, 222 126, 228 118", 4.0),
    ("M200 150 C194 170, 190 190, 188 206", 4.0),
    ("M138 150 C132 164, 140 176, 152 186", 3.5),
    ("M152 186 C140 192, 126 190, 118 188 C106 186, 98 196, 102 208", 2.6),
    ("M248 154 C246 168, 240 180, 230 188", 3.5),
    ("M230 188 C238 198, 248 204, 258 202 C266 200, 270 208, 266 214", 2.6),
)

ICON_NODULES = (
    (200, 150, 8.0, 7.0),
    (170, 122, 5.2, 4.6),
    (138, 150, 5.2, 4.8),
    (152, 186, 5.0, 5.4),
    (188, 206, 5.2, 4.6),
    (230, 188, 5.0, 5.4),
    (248, 154, 5.2, 4.6),
    (228, 118, 5.0, 5.2),
)

# Nutrient packet motion (same routes as the previous hard-coded animateMotion).
PACKET_PATH_LEFT = (
    "M200 150 C178 148, 158 148, 138 150 "
    "C132 164, 140 176, 152 186 "
    "C140 192, 126 190, 118 188 C106 186, 98 196, 102 208"
)
PACKET_PATH_RIGHT = (
    "M200 150 C218 148, 234 150, 248 154 "
    "C246 168, 240 180, 230 188 "
    "C238 198, 248 204, 258 202"
)
