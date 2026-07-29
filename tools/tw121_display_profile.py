#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prépare un profil d'affichage pour les validations manuelles TW-121.

L'outil ne recherche pas arbitrairement la configuration : le chemin du fichier
Customize.ini doit être fourni explicitement afin d'éviter de modifier une autre
installation Teamworks/Noethys présente sur le poste.
"""

from __future__ import annotations

import argparse
import configparser
import shutil
from datetime import datetime
from pathlib import Path

THEMES = {
    "systeme": "Systeme",
    "système": "Systeme",
    "system": "Systeme",
    "clair": "Clair",
    "light": "Clair",
    "sombre": "Sombre",
    "dark": "Sombre",
}
MIN_SCALE = 80
MAX_SCALE = 200


def normalize_theme(value: str) -> str:
    try:
        return THEMES[value.strip().lower()]
    except KeyError as exc:
        choices = "Système, Clair ou Sombre"
        raise ValueError(f"Thème invalide : {value!r}. Valeurs admises : {choices}.") from exc


def normalize_scale(value: int) -> int:
    if not MIN_SCALE <= value <= MAX_SCALE:
        raise ValueError(f"Échelle invalide : {value}. Valeurs admises : {MIN_SCALE} à {MAX_SCALE} %.")
    return value


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.tw121-{timestamp}.bak")
    shutil.copy2(path, backup)
    return backup


def apply_profile(path: Path, theme: str, scale: int) -> Path | None:
    theme = normalize_theme(theme)
    scale = normalize_scale(scale)

    parser = configparser.ConfigParser()
    if path.exists():
        parser.read(path, encoding="utf-8")
    if not parser.has_section("interface"):
        parser.add_section("interface")

    backup = backup_file(path)
    parser.set("interface", "theme", theme)
    parser.set("interface", "echelle_police", str(scale))

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        parser.write(stream)
    return backup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prépare Customize.ini pour une validation d'affichage TW-121."
    )
    parser.add_argument("config", type=Path, help="Chemin explicite vers Customize.ini")
    parser.add_argument("--theme", required=True, help="Système, Clair ou Sombre")
    parser.add_argument("--scale", required=True, type=int, help="Échelle de police entre 80 et 200")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        backup = apply_profile(args.config, args.theme, args.scale)
    except (OSError, ValueError) as exc:
        print(f"ERREUR : {exc}")
        return 2

    print(f"Profil appliqué : {normalize_theme(args.theme)} / {args.scale} %")
    print(f"Configuration : {args.config}")
    if backup:
        print(f"Sauvegarde : {backup}")
    else:
        print("Sauvegarde : aucune, le fichier n'existait pas")
    print("Relancer Teamworks-CCNS pour appliquer le profil.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
