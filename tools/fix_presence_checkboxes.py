#!/usr/bin/env python3
"""Active explicitement les cases à cocher des listes de présence sous Phoenix."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENCODING = "iso-8859-15"
TARGETS = (
    ROOT / "teamworks" / "Ctrl" / "CTRL_Presences.py",
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py",
)

ANCHOR = """        CheckListCtrlMixin.__init__(self)
        self.parent = parent
"""
REPLACEMENT = """        CheckListCtrlMixin.__init__(self)
        if 'phoenix' in wx.PlatformInfo:
            self.EnableCheckBoxes(True)
        self.parent = parent
"""
EXPECTED = """        if 'phoenix' in wx.PlatformInfo:
            self.EnableCheckBoxes(True)
"""


def correct(path: Path) -> bool:
    source = path.read_text(encoding=ENCODING)
    if EXPECTED in source:
        compile(source, str(path), "exec")
        print(f"{path.name} active déjà les cases Phoenix")
        return False

    count = source.count(ANCHOR)
    if count != 1:
        raise RuntimeError(f"ancre checkbox absente ou ambiguë dans {path}: count={count}")

    updated = source.replace(ANCHOR, REPLACEMENT, 1)
    if updated.count(EXPECTED) != 1:
        raise RuntimeError(f"activation checkbox non insérée exactement une fois dans {path}")

    compile(updated, str(path), "exec")
    path.write_text(updated, encoding=ENCODING)
    print(f"{path.name} corrigé : cases à cocher Phoenix activées")
    return True


def main() -> int:
    changed = [path for path in TARGETS if correct(path)]
    if not changed:
        print("Aucune correction supplémentaire nécessaire")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
