#!/usr/bin/env python3
"""Génère l'icône Teamworks-CCNS depuis la charte de pelemele.org."""

from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "teamworks" / "Static" / "Images" / "Branding" / "Teamworks-CCNS.png"
STATIC_ICO = ROOT / "teamworks" / "Static" / "Images" / "Branding" / "Teamworks-CCNS.ico"
LEGACY_ICO = ROOT / "teamworks" / "Icone.ico"
WINDOW_ICON = ROOT / "teamworks" / "Static" / "Images" / "16x16" / "Logo.png"

PELEMELE_ORANGE = "#FFBD59"
PELEMELE_SLATE = "#314666"
PELEMELE_DEEP_BLUE = "#044576"
OFF_WHITE = "#FFFDF7"


def _font_path() -> Path:
    candidates = (
        Path("C:/Windows/Fonts/seguisb.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Aucune police sans serif grasse adaptée à l'icône")


def _centered_text(draw, area, text, font, fill):
    left, top, right, bottom = area
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x = left + (right - left - width) / 2 - bounds[0]
    y = top + (bottom - top - height) / 2 - bounds[1]
    draw.text((x, y), text, font=font, fill=fill)


def generate():
    font_path = _font_path()
    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (48, 48, 976, 976),
        radius=210,
        fill=PELEMELE_SLATE,
        outline=PELEMELE_DEEP_BLUE,
        width=22,
    )
    _centered_text(
        draw,
        (110, 125, 914, 660),
        "TW",
        ImageFont.truetype(str(font_path), 470),
        PELEMELE_ORANGE,
    )
    _centered_text(
        draw,
        (150, 650, 874, 865),
        "CCNS",
        ImageFont.truetype(str(font_path), 170),
        OFF_WHITE,
    )

    MASTER.parent.mkdir(parents=True, exist_ok=True)
    image.save(MASTER, optimize=True)
    image.save(
        STATIC_ICO,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
               (96, 96), (128, 128), (256, 256)],
    )
    shutil.copyfile(STATIC_ICO, LEGACY_ICO)
    image.resize((16, 16), Image.Resampling.LANCZOS).save(WINDOW_ICON, optimize=True)

    print(MASTER.relative_to(ROOT))
    print(STATIC_ICO.relative_to(ROOT))
    print(LEGACY_ICO.relative_to(ROOT))
    print(WINDOW_ICON.relative_to(ROOT))


if __name__ == "__main__":
    generate()
