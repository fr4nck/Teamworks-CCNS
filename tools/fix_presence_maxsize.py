#!/usr/bin/env python3
"""Corrige les insertions de fin de liste incompatibles avec wxPython Phoenix."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENCODING = "iso-8859-15"
TARGETS = (
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py",
    ROOT / "teamworks" / "Ctrl" / "CTRL_Presences.py",
)

REPLACEMENTS = {
    "self.InsertItem(six.MAXSIZE,": "self.InsertItem(self.GetItemCount(),",
    "self.InsertItem(sys.maxsize,": "self.InsertItem(self.GetItemCount(),",
    "self.InsertStringItem(six.MAXSIZE,": "self.InsertStringItem(self.GetItemCount(),",
    "self.InsertStringItem(sys.maxsize,": "self.InsertStringItem(self.GetItemCount(),",
}

FORBIDDEN = (
    "InsertItem(six.MAXSIZE,",
    "InsertItem(sys.maxsize,",
    "InsertStringItem(six.MAXSIZE,",
    "InsertStringItem(sys.maxsize,",
)


def correct(path: Path) -> bool:
    source = path.read_text(encoding=ENCODING)
    updated = source
    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)

    for token in FORBIDDEN:
        if token in updated:
            raise RuntimeError(f"insertion wxPython encore incompatible dans {path}: {token}")

    compile(updated, str(path), "exec")
    if updated == source:
        print(f"{path.name} est déjà corrigé")
        return False

    path.write_text(updated, encoding=ENCODING)
    print(f"{path.name} corrigé : insertion explicite à GetItemCount()")
    return True


def main() -> int:
    changed = [path for path in TARGETS if correct(path)]
    if not changed:
        print("Aucune correction supplémentaire nécessaire")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
