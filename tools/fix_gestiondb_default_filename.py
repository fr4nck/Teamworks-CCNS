#!/usr/bin/env python3
"""Restaure la résolution du fichier courant dans GestionDB.DB."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "GestionDB.py"
ENCODING = "iso-8859-15"

ANCHOR = """        DICT_CONNEXIONS[self.IDconnexion] = []

        # On ajoute le préfixe de type de fichier et l'extension du fichier
"""
REPLACEMENT = """        DICT_CONNEXIONS[self.IDconnexion] = []

        # Si aucun nom de fichier n'est spécifié, on recherche celui par défaut
        # dans la configuration de la fenêtre principale.
        if self.nomFichier == "":
            self.nomFichier = self.GetNomFichierDefaut()

        # On ajoute le préfixe de type de fichier et l'extension du fichier
"""


def main() -> int:
    source = TARGET.read_text(encoding=ENCODING)

    expected = 'if self.nomFichier == "":\n            self.nomFichier = self.GetNomFichierDefaut()'
    if expected in source:
        print("GestionDB.DB résout déjà le fichier courant")
        return 0

    if source.count(ANCHOR) != 1:
        raise RuntimeError("ancre GestionDB.DB introuvable ou ambiguë")

    updated = source.replace(ANCHOR, REPLACEMENT, 1)
    compile(updated, str(TARGET), "exec")
    TARGET.write_text(updated, encoding=ENCODING)
    print("GestionDB.DB : résolution du fichier courant restaurée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
