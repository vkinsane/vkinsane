"""Hand-author the neofetch-style info card SVG.

A title bar plus colored key/value rows, each fading and sliding in on
a short stagger. Set STATIC=1 to freeze the animation for local preview
(e.g. an OS screenshot tool that can't capture SMIL mid-play).

Usage: python scripts/make_info_card.py
"""
import os
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUTPUT_PATH = ASSETS / "info-card.svg"

WIDTH = 490
ROW_H = 30
TITLE_H = 40
PADDING_X = 20

BG = "#0d1117"
TITLE_BG = "#161b22"
BORDER = "#30363d"
KEY_COLOR = "#58a6ff"
VALUE_COLOR = "#c9d1d9"
TITLE_COLOR = "#e6edf3"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]

ROW_STAGGER_S = 0.12
FADE_DURATION_S = 0.5

ROWS = [
    ("Now", "Software Engineer (Frontend), OnlineSales.ai"),
    ("Prev", "Zipy.ai (Fullstack) · NielsenIQ (Intern)"),
    ("Stack", "React, Node.js, Java, Spring Boot, BigQuery"),
    ("Shipped", "Osmos-Reach: 7% → 45% marketplace fill rate"),
    ("Verified", "DCM/Adobe SDK — 1M+ monthly impressions"),
    ("Wins", "2x hackathon winner (Zipy.ai, HackMoriesh)"),
    ("OSS", "Contributor — rrweb, ApexCharts"),
]


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_svg(static: bool) -> str:
    height = TITLE_H + ROW_H * len(ROWS) + 16

    dots = "".join(
        f'<circle cx="{20 + i * 16}" cy="{TITLE_H / 2}" r="5" fill="{color}" />'
        for i, color in enumerate(DOT_COLORS)
    )

    rows_svg = []
    for i, (key, value) in enumerate(ROWS):
        y = TITLE_H + 24 + i * ROW_H
        row_group_start = f'<g opacity="{1 if static else 0}" transform="translate(0,0)">'
        if not static:
            begin = round(i * ROW_STAGGER_S, 3)
            animations = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'dur="{FADE_DURATION_S}s" begin="{begin}s" fill="freeze" />'
            )
        else:
            animations = ""

        rows_svg.append(
            f"{row_group_start}{animations}"
            f'<text x="{PADDING_X}" y="{y}" font-family="Menlo, Consolas, monospace" '
            f'font-size="14" font-weight="600" fill="{KEY_COLOR}">{escape_xml(key)}</text>'
            f'<text x="{PADDING_X + 90}" y="{y}" font-family="Menlo, Consolas, monospace" '
            f'font-size="13" fill="{VALUE_COLOR}">{escape_xml(value)}</text>'
            f"</g>"
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}">'
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}" />'
        f'<path d="M0.5,{TITLE_H} v-{TITLE_H - 8} a8,8 0 0 1 8,-8 h{WIDTH - 17} '
        f'a8,8 0 0 1 8,8 v{TITLE_H - 8} z" fill="{TITLE_BG}" />'
        f'<line x1="0" y1="{TITLE_H}" x2="{WIDTH}" y2="{TITLE_H}" stroke="{BORDER}" />'
        f"{dots}"
        f'<text x="{WIDTH / 2}" y="{TITLE_H / 2 + 5}" font-family="Menlo, Consolas, monospace" '
        f'font-size="13" fill="{TITLE_COLOR}" text-anchor="middle">vishal@github: ~</text>'
        f"{''.join(rows_svg)}"
        f"</svg>"
    )


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static)
    ASSETS.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg)
    print(f"Saved info card to {OUTPUT_PATH}{' (static)' if static else ''}")


if __name__ == "__main__":
    main()
