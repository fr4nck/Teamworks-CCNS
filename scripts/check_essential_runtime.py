#!/usr/bin/env python3
"""Vérifie le socle minimal nécessaire à une version Windows exploitable.

Ce contrôle reste volontairement structurel : il détecte les fichiers absents,
les ressources principales manquantes et les sources Python non compilables
avant de lancer PyInstaller.
"""

from __future__ import annotations

import py_compile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

ESSENTIAL_PYTHON_FILES = (
    "teamworks/Teamworks.py",
    "teamworks/Chemins.py",
    "teamworks/GestionDB.py",
    "teamworks/UpgradeDB.py",
    "teamworks/Ctrl/CTRL_Accueil.py",
    "teamworks/Ctrl/CTRL_Personnes.py",
    "teamworks/Ctrl/CTRL_Presences.py",
    "teamworks/Ctrl/CTRL_Recrutement.py",
)

ESSENTIAL_RESOURCES = (
    "teamworks/Static/Images/32x32/Maison.png",
    "teamworks/Static/Images/32x32/Personnes.png",
    "teamworks/Static/Images/32x32/Horloge.png",
    "teamworks/Static/Images/32x32/Recrutement.png",
)


def check_exists(relative_path: str) -> Path:
    path = REPOSITORY_ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Composant essentiel absent : {relative_path}")
    return path


def main() -> int:
    for relative_path in ESSENTIAL_PYTHON_FILES:
        source_path = check_exists(relative_path)
        py_compile.compile(str(source_path), doraise=True)

    for relative_path in ESSENTIAL_RESOURCES:
        resource_path = check_exists(relative_path)
        if resource_path.stat().st_size == 0:
            raise RuntimeError(f"Ressource essentielle vide : {relative_path}")

    print(
        "Socle essentiel valide : "
        f"{len(ESSENTIAL_PYTHON_FILES)} modules Python et "
        f"{len(ESSENTIAL_RESOURCES)} ressources contrôlés."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
