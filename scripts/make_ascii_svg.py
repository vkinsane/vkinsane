"""Convert the prepped grayscale portrait into an animated ASCII-art SVG.

Downsamples the image to a character grid, maps brightness to a ramp,
and draws each row as monospace SVG text with a staggered left-to-right
SMIL wipe that plays once.

Usage: python scripts/make_ascii_svg.py
"""
from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SOURCE_PATH = ASSETS / "source-prepped.png"
OUTPUT_PATH = ASSETS / "vishal-ascii.svg"

# Dark -> light. Index into this ramp by brightness.
RAMP = " .:-=+*cs#%@"[::-1]

COLS = 100
ROWS = 67  # matches the 303x356 source aspect ratio against an 8x14 char cell
CHAR_W = 8
CHAR_H = 14
FONT_SIZE = 13
FILL_COLOR = "#8b949e"
BG_COLOR = "#0d1117"
ROW_STAGGER_S = 0.035
WIPE_DURATION_S = 0.6


def load_brightness_grid(path: Path) -> list:
    img = Image.open(path).convert("L")
    # Character cells are taller than wide, so squash vertically to
    # keep the portrait's proportions when sampled onto the grid.
    resized = img.resize((COLS, ROWS))
    pixels = list(resized.getdata())
    return [pixels[r * COLS:(r + 1) * COLS] for r in range(ROWS)]


def brightness_to_char(value: int) -> str:
    idx = int((value / 255) * (len(RAMP) - 1))
    return RAMP[idx]


def row_to_ascii(row: list) -> str:
    return "".join(brightness_to_char(v) for v in row)


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_svg(rows: list) -> str:
    width = COLS * CHAR_W
    height = ROWS * CHAR_H

    text_elements = []
    clip_defs = []
    for i, row in enumerate(rows):
        ascii_row = row_to_ascii(row)
        y = (i + 1) * CHAR_H - 2
        clip_id = f"wipe{i}"
        begin = round(i * ROW_STAGGER_S, 3)

        clip_defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{i * CHAR_H}" width="0" height="{CHAR_H}">'
            f'<animate attributeName="width" from="0" to="{width}" '
            f'dur="{WIPE_DURATION_S}s" begin="{begin}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1" />'
            f"</rect></clipPath>"
        )
        text_elements.append(
            f'<text x="0" y="{y}" font-family="Menlo, Consolas, monospace" '
            f'font-size="{FONT_SIZE}" fill="{FILL_COLOR}" xml:space="preserve" '
            f'clip-path="url(#{clip_id})">{escape_xml(ascii_row)}</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="{BG_COLOR}" />'
        f"<defs>{''.join(clip_defs)}</defs>"
        f"{''.join(text_elements)}"
        f"</svg>"
    )


def main() -> None:
    if not SOURCE_PATH.exists():
        print(f"Missing {SOURCE_PATH}. Run scripts/prep_photo.py first.")
        raise SystemExit(1)

    rows = load_brightness_grid(SOURCE_PATH)
    svg = build_svg(rows)
    OUTPUT_PATH.write_text(svg)
    print(f"Saved ASCII portrait to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
