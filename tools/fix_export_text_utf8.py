#!/usr/bin/env python3
"""Corrige l'écriture Python 3 de l'export texte Teamworks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Utils" / "UTILS_Export.py"
ENCODING = "iso-8859-15"
OLD = '    f = open(cheminFichier, "w")\n    f.write(texte.encode("utf8"))\n    f.close()'
NEW = '    with open(cheminFichier, "w", encoding="utf-8", newline="") as fichier:\n        fichier.write(texte)'


def main() -> int:
    source = TARGET.read_text(encoding=ENCODING)
    if NEW in source:
        print("ExportTexte utilise déjà une écriture UTF-8 native")
        return 0
    if source.count(OLD) != 1:
        raise RuntimeError("bloc d'écriture historique introuvable ou ambigu")
    updated = source.replace(OLD, NEW, 1)
    compile(updated, str(TARGET), "exec")
    TARGET.write_text(updated, encoding=ENCODING)
    print("ExportTexte corrigé pour Python 3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
