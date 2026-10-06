"""Prepare a source photo for ASCII-art conversion.

Removes the background, boosts contrast, composites onto pure white,
and saves a grayscale PNG that make_ascii_svg.py can consume.

Usage: python scripts/prep_photo.py <source-photo.jpg>
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ASSETS = Path(__file__).resolve().parent.parent / "assets"
OUTPUT_PATH = ASSETS / "source-prepped.png"


def remove_background(src_path: Path) -> Image.Image:
    with open(src_path, "rb") as f:
        result = remove(f.read())
    return Image.open(__import__("io").BytesIO(result)).convert("RGBA")


def boost_contrast(rgba: Image.Image) -> Image.Image:
    rgb = np.array(rgba.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(16, 16))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    rgb_boosted = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    boosted = Image.fromarray(rgb_boosted).convert("RGBA")
    boosted.putalpha(rgba.getchannel("A"))
    return boosted


def composite_on_white(rgba: Image.Image) -> Image.Image:
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(white_bg, rgba).convert("RGB")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/prep_photo.py <source-photo.jpg>")
        sys.exit(1)

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"Source photo not found: {src_path}")
        sys.exit(1)

    no_bg = remove_background(src_path)
    contrasted = boost_contrast(no_bg)
    composited = composite_on_white(contrasted)
    grayscale = composited.convert("L")

    ASSETS.mkdir(parents=True, exist_ok=True)
    grayscale.save(OUTPUT_PATH)
    print(f"Saved prepped portrait to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
