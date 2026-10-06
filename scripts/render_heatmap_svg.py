"""Render data/contributions.json as an animated heatmap SVG.

Draws a 53x7 grid of rounded boxes with a diagonal CSS-keyframe reveal
(plays once), a legend, and a stats footer.

Usage: python scripts/render_heatmap_svg.py
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "contrib-heatmap.svg"

CELL = 11
GAP = 3
STEP = CELL + GAP
COLS = 53
ROWS = 7
MARGIN_LEFT = 20
MARGIN_TOP = 20
FOOTER_H = 50
LEGEND_H = 20

BG = "#0d1117"
TEXT_COLOR = "#8b949e"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

REVEAL_DURATION_S = 1.4


def level_for_count(count: int, max_count: int) -> int:
    if count <= 0:
        return 0
    if max_count <= 0:
        return 1
    ratio = count / max_count
    if ratio > 0.75:
        return 5
    if ratio > 0.5:
        return 4
    if ratio > 0.25:
        return 3
    return 2


def pad_to_full_weeks(days: list) -> list:
    if not days:
        return days
    first_date = days[0]["date"]
    import datetime

    first = datetime.date.fromisoformat(first_date)
    # GitHub's calendar starts weeks on Sunday.
    lead_padding = (first.weekday() + 1) % 7
    padded = [{"date": None, "count": -1}] * lead_padding + days
    return padded


def build_svg(summary: dict) -> str:
    days = pad_to_full_weeks(summary["days"])
    max_count = max((d["count"] for d in summary["days"]), default=0)

    width = MARGIN_LEFT + COLS * STEP + 140
    height = MARGIN_TOP + ROWS * STEP + LEGEND_H + FOOTER_H

    cells = []
    week = 0
    day_of_week = 0
    cell_index = 0
    for day in days:
        x = MARGIN_LEFT + week * STEP
        y = MARGIN_TOP + day_of_week * STEP

        if day["count"] >= 0:
            level = level_for_count(day["count"], max_count)
            color = PALETTE[level]
            delay = round((week + day_of_week) * 0.012, 3)
            title = f'{day["count"]} contributions on {day["date"]}'
            cells.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" class="cell" style="animation-delay:{delay}s">'
                f"<title>{title}</title></rect>"
            )

        day_of_week += 1
        if day_of_week == 7:
            day_of_week = 0
            week += 1
        cell_index += 1

    legend_y = MARGIN_TOP + ROWS * STEP + 14
    legend_x = MARGIN_LEFT
    legend_cells = []
    for i, color in enumerate(PALETTE):
        lx = legend_x + 40 + i * (CELL + 4)
        legend_cells.append(
            f'<rect x="{lx}" y="{legend_y - 9}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{color}" />'
        )
    legend_svg = (
        f'<text x="{legend_x}" y="{legend_y}" font-family="Menlo, Consolas, monospace" '
        f'font-size="11" fill="{TEXT_COLOR}">Less</text>'
        f"{''.join(legend_cells)}"
        f'<text x="{legend_x + 40 + len(PALETTE) * (CELL + 4) + 6}" y="{legend_y}" '
        f'font-family="Menlo, Consolas, monospace" font-size="11" fill="{TEXT_COLOR}">More</text>'
    )

    footer_y = legend_y + 26
    footer_text = (
        f'{summary["total_contributions"]} contributions in the last year   •   '
        f'current streak {summary["current_streak"]}d   •   '
        f'longest streak {summary["longest_streak"]}d   •   '
        f'best day {summary["best_day"]["count"]} on {summary["best_day"]["date"]}'
    )
    footer_svg = (
        f'<text x="{MARGIN_LEFT}" y="{footer_y}" font-family="Menlo, Consolas, monospace" '
        f'font-size="12" fill="{TEXT_COLOR}">{footer_text}</text>'
    )

    style = (
        "<style>"
        ".cell{opacity:0;animation:reveal 0.01s ease-out forwards;"
        f"animation-duration:{REVEAL_DURATION_S}s;}}"
        "@keyframes reveal{0%{opacity:0;transform:scale(0.3);}"
        "100%{opacity:1;transform:scale(1);}}"
        "rect.cell{transform-box:fill-box;transform-origin:center;}"
        "</style>"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f"{style}"
        f'<rect width="{width}" height="{height}" fill="{BG}" />'
        f"{''.join(cells)}"
        f"{legend_svg}"
        f"{footer_svg}"
        f"</svg>"
    )


def main() -> None:
    if not DATA_PATH.exists():
        print(f"Missing {DATA_PATH}. Run scripts/fetch_contributions.py first.")
        raise SystemExit(1)

    summary = json.loads(DATA_PATH.read_text())
    svg = build_svg(summary)
    OUTPUT_PATH.write_text(svg)
    print(f"Saved heatmap to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
