#!/usr/bin/env python3
"""Remplace les usages résiduels de six.MAXSIZE dans le formulaire de présence."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py"
ENCODING = "iso-8859-15"

REPLACEMENTS = {
    'self.InsertItem(six.MAXSIZE, "")': 'self.InsertItem(sys.maxsize, "")',
    'self.InsertStringItem(six.MAXSIZE, "")': 'self.InsertStringItem(sys.maxsize, "")',
}


def main() -> int:
    source = TARGET.read_text(encoding=ENCODING)
    updated = source
    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)

    if "six.MAXSIZE" in updated:
        raise RuntimeError("des usages de six.MAXSIZE subsistent dans DLG_Saisie_presence.py")
    if 'self.InsertItem(sys.maxsize, "")' not in updated:
        raise RuntimeError("l’insertion Phoenix via sys.maxsize est absente")

    if updated == source:
        print("DLG_Saisie_presence.py est déjà corrigé")
        return 0

    TARGET.write_text(updated, encoding=ENCODING)
    print("DLG_Saisie_presence.py corrigé : six.MAXSIZE -> sys.maxsize")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
