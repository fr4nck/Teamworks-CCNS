#!/usr/bin/env python3
"""Décline le master du logo Teamworks-CCNS pour Windows et wxPython."""

from __future__ import annotations

from pathlib import Path
import shutil

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "teamworks" / "Static" / "Images" / "Branding" / "Teamworks-CCNS.png"
STATIC_ICO = ROOT / "teamworks" / "Static" / "Images" / "Branding" / "Teamworks-CCNS.ico"
LEGACY_ICO = ROOT / "teamworks" / "Icone.ico"
WINDOW_ICON = ROOT / "teamworks" / "Static" / "Images" / "16x16" / "Logo.png"

PELEMELE_ORANGE = "#FFBD59"
PELEMELE_SLATE = "#314666"
PELEMELE_DEEP_BLUE = "#044576"
OFF_WHITE = "#FFFDF7"

# Le master approuvé porte les libellés exacts "TW" et "CCNS". Il reste la
# source de vérité afin que les déclinaisons ne dépendent pas des polices de la
# machine qui exécute le packaging.


def generate():
    if not MASTER.is_file():
        raise FileNotFoundError(f"Master du logo introuvable : {MASTER}")

    with Image.open(MASTER) as source:
        image = source.convert("RGBA")

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
