#!/usr/bin/env python3
"""Restaure la résolution du fichier courant dans GestionDB.DB."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "GestionDB.py"
ENCODING = "iso-8859-15"

ANCHOR = """        DICT_CONNEXIONS[self.IDconnexion] = []

        # On ajoute le pr"""
INSERTION = """        DICT_CONNEXIONS[self.IDconnexion] = []

        # Resolve the active Teamworks file when callers omit nomFichier.
        if self.nomFichier == "":
            self.nomFichier = self.GetNomFichierDefaut()

        # On ajoute le pr"""
EXPECTED = """        if self.nomFichier == "":
            self.nomFichier = self.GetNomFichierDefaut()
"""


def main() -> int:
    source = TARGET.read_text(encoding=ENCODING)

    if EXPECTED in source:
        print("GestionDB.DB resolves the current file already")
        return 0

    anchor_count = source.count(ANCHOR)
    if anchor_count != 1:
        raise RuntimeError(
            f"stable GestionDB.DB anchor missing or ambiguous: count={anchor_count}"
        )

    updated = source.replace(ANCHOR, INSERTION, 1)
    if updated.count(EXPECTED) != 1:
        raise RuntimeError("default filename block was not inserted exactly once")
    if updated.index(EXPECTED) > updated.index("if MODE_TEAMWORKS == True"):
        raise RuntimeError("default filename resolution was inserted after suffix handling")

    compile(updated, str(TARGET), "exec")
    TARGET.write_text(updated, encoding=ENCODING)
    print("GestionDB.DB current-file resolution restored")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
