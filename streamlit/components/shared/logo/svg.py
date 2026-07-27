"""SVG / HTML builders for the brand mark (static assets + Home animation)."""

from __future__ import annotations

import base64

from components.shared.logo.geometry import (
    FLOW,
    HERO_VIEWBOX,
    ICON_NODULES,
    ICON_PATHS,
    ICON_VIEWBOX,
    INK,
    LOGO_HEADER_DARK,
    LOGO_HEADER_LIGHT,
    LOGO_SIDEBAR,
    MARK_VIEWBOX,
    NODULES,
    PACKET_PATH_LEFT,
    PACKET_PATH_RIGHT,
    PATHS,
    WORDMARK_VIEWBOX,
)
from components.shared.logo.wordmark_glyphs import WORDMARK_LETTER_PATHS


def svg_data_uri(svg: str) -> str:
    payload = base64.standard_b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{payload}"


def _stroke_group(paths: tuple, ink: str) -> str:
    lines = [
        f'  <g fill="none" stroke="{ink}" stroke-linecap="round" stroke-linejoin="round">'
    ]
    for item in paths:
        d, width = item[0], item[1]
        lines.append(f'    <path d="{d}" stroke-width="{width}"/>')
    lines.append("  </g>")
    return "\n".join(lines)


def _bead_group(nodules: tuple, ink: str, *, named: bool = False) -> str:
    lines = [f'  <g fill="{ink}">']
    for entry in nodules:
        if named:
            _name, cx, cy, rx, ry = entry
        else:
            cx, cy, rx, ry = entry
        lines.append(f'    <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>')
    lines.append("  </g>")
    return "\n".join(lines)


def build_mark_svg(*, ink: str = INK, view_box: str = MARK_VIEWBOX) -> str:
    return "\n".join(
        (
            f'<svg viewBox="{view_box}" xmlns="http://www.w3.org/2000/svg" '
            'role="img" aria-label="Agro Tech">',
            _stroke_group(PATHS, ink),
            _bead_group(NODULES, ink, named=True),
            "</svg>",
            "",
        )
    )


def build_icon_svg(*, ink: str = INK) -> str:
    return "\n".join(
        (
            f'<svg viewBox="{ICON_VIEWBOX}" xmlns="http://www.w3.org/2000/svg" '
            'role="img" aria-label="Agro Tech">',
            _stroke_group(ICON_PATHS, ink),
            _bead_group(ICON_NODULES, ink, named=False),
            "</svg>",
            "",
        )
    )


def build_wordmark_svg(*, ink: str = LOGO_SIDEBAR) -> str:
    letters = "\n".join(f'    <path d="{d}"/>' for d in WORDMARK_LETTER_PATHS)
    return "\n".join(
        (
            f'<svg viewBox="{WORDMARK_VIEWBOX}" xmlns="http://www.w3.org/2000/svg" '
            'role="img" aria-label="Agro Tech">',
            _stroke_group(PATHS, ink),
            _bead_group(NODULES, ink, named=True),
            f'  <g fill="{ink}">',
            letters,
            "  </g>",
            "</svg>",
            "",
        )
    )


LOGO_MEANING_PLAIN = (
    "A logo da Agro Tech foi inspirada no sistema radicular da soja. "
    "As linhas representam as raizes, simbolizando a origem, a integracao "
    "e a rastreabilidade de toda a cadeia produtiva. As esferas distribuídas "
    "ao longo das raizes representam os nodulos radiculares, estruturas "
    "naturais da soja que abrigam bacterias responsaveis pela fixacao "
    "biologica de nitrogenio, essencial para o desenvolvimento da planta. "
    "Na identidade da Agro Tech, esses nodulos tambem simbolizam os dados "
    "e os modulos do sistema, conectados por uma mesma base de informacoes. "
    "Assim como a raiz sustenta e alimenta a planta, a plataforma integra "
    "Producao, Estoque, Logistica, Comercial, Financeiro, Fitossanidade, Manutençao e Inteligencia, "
    "fornecendo uma gestao unificada e rastreavel do agronegocio."
)

LOGO_MEANING_MARKDOWN = """
A logo da **Agro Tech** foi inspirada no sistema radicular da soja. As linhas
representam as raízes, simbolizando a origem, a integração e a rastreabilidade
de toda a cadeia produtiva. As esferas distribuídas ao longo das raízes
representam os **nódulos radiculares**, estruturas naturais da soja que
abrigam bactérias responsáveis pela fixação biológica de nitrogênio, essencial
para o desenvolvimento da planta. Na identidade da Agro Tech, esses nódulos
também simbolizam os dados e os módulos do sistema, conectados por uma mesma
base de informações. Assim como a raiz sustenta e alimenta a planta, a
plataforma integra Produção, Estoque, Logística, Comercial, Financeiro, Fitossanidade, Manutenção e
Inteligência, fornecendo uma gestão unificada e rastreável do agronegócio.
"""


def build_animated_document(
    *,
    width: int = 300,
    animated: bool = True,
    ink: str = INK,
    flow: str = FLOW,
) -> str:
    mode = "is-animated" if animated else "is-static"

    paths = [
        f'<path class="stroke" d="{d}" style="--w:{w};--len:{length};--d:{delay}s"/>'
        for d, w, length, delay in PATHS
    ]

    beads: list[str] = []
    for i, (name, cx, cy, rx, ry) in enumerate(NODULES):
        if i == 0:
            appear, glow = 0.06, 3.60
        else:
            appear = 1.70 + (i - 1) * 0.10
            glow = 3.75 + (i - 1) * 0.11
        beads.append(
            f'<g class="bead" style="--a:{appear:.2f}s;--g:{glow:.2f}s">'
            f"<title>{name}</title>"
            f'<ellipse class="bead-core" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/>'
            f"</g>"
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  html, body {{
    margin: 0; padding: 0; background: transparent;
    width: 100%; height: 100%;
    display: flex; justify-content: center; align-items: center;
  }}
  svg {{ display: block; cursor: help; }}

  .stroke {{
    fill: none;
    stroke: {ink};
    stroke-width: var(--w);
    stroke-linecap: round;
    stroke-linejoin: round;
  }}
  .bead-core {{ fill: {ink}; }}
  .packet {{ fill: {flow}; }}

  .bead, .packet, .stroke {{
    transform-box: fill-box;
    transform-origin: center;
  }}

  .is-static .stroke {{ stroke-dasharray: none; stroke-dashoffset: 0; }}
  .is-static .bead {{ opacity: 1; transform: scale(1); }}
  .is-static .packet {{ opacity: 0; }}

  .is-animated .bead {{
    opacity: 0; transform: scale(0);
    animation: pop 0.42s cubic-bezier(.34,1.4,.64,1) var(--a) forwards;
  }}
  .is-animated .stroke {{
    stroke-dasharray: var(--len);
    stroke-dashoffset: var(--len);
    animation: draw 1.2s cubic-bezier(.4,0,.2,1) var(--d) forwards;
  }}
  .is-animated .bead-core {{
    animation: glow 0.8s ease-in-out var(--g) 1;
  }}
  .is-animated .packet {{
    opacity: 0;
    animation: packet 1.9s ease 3.25s forwards;
  }}

  @keyframes pop {{ to {{ opacity: 1; transform: scale(1); }} }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  @keyframes glow {{
    0%   {{ fill: {ink}; filter: drop-shadow(0 0 0 {flow}); }}
    45%  {{ fill: {flow}; filter: drop-shadow(0 0 7px {flow}); }}
    100% {{ fill: {ink}; filter: drop-shadow(0 0 0 {flow}); }}
  }}
  @keyframes packet {{
    0% {{ opacity: 0; }} 12% {{ opacity: 1; }} 80% {{ opacity: 1; }} 100% {{ opacity: 0; }}
  }}

  @media (prefers-reduced-motion: reduce) {{
    .is-animated .stroke, .is-animated .bead, .is-animated .bead-core,
    .is-animated .packet {{ animation: none !important; }}
    .is-animated .bead {{ opacity: 1; transform: scale(1); }}
    .is-animated .stroke {{ stroke-dashoffset: 0; }}
    .is-animated .packet {{ opacity: 0; }}
  }}
</style>
</head>
<body>
<svg class="{mode}" viewBox="{HERO_VIEWBOX}" width="{width}" height="auto"
     role="img" aria-label="Agro Tech" xmlns="http://www.w3.org/2000/svg">
  <title>{LOGO_MEANING_PLAIN}</title>
  {"".join(paths)}

  <circle class="packet" r="3.1">
    <animateMotion dur="1.9s" begin="3.25s" fill="freeze"
      path="{PACKET_PATH_LEFT}"/>
  </circle>
  <circle class="packet" r="2.7">
    <animateMotion dur="1.5s" begin="3.55s" fill="freeze"
      path="{PACKET_PATH_RIGHT}"/>
  </circle>

  {"".join(beads)}
</svg>
</body></html>
"""


def sidebar_logo_uris(*, theme: str = "light") -> tuple[str, str]:
    """Wordmark + icon for ``st.logo`` (top-left only).

    - Sidebar open (dark teal): soft green wordmark
    - Sidebar collapsed: primary green on light chrome, accent green on dark
    """
    wordmark = svg_data_uri(build_wordmark_svg(ink=LOGO_SIDEBAR))
    header_ink = LOGO_HEADER_DARK if theme == "dark" else LOGO_HEADER_LIGHT
    icon = svg_data_uri(build_icon_svg(ink=header_ink))
    return wordmark, icon
