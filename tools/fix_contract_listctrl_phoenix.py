#!/usr/bin/env python3
"""Corrige la liste des champs du contrat pour wxPython Phoenix."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p4.py"
ENCODING = "iso-8859-15"

REPLACEMENTS = {
    "self.InsertItem(six.MAXSIZE,": "self.InsertItem(self.GetItemCount(),",
    "self.InsertItem(sys.maxsize,": "self.InsertItem(self.GetItemCount(),",
    "self.InsertStringItem(six.MAXSIZE,": "self.InsertStringItem(self.GetItemCount(),",
    "self.InsertStringItem(sys.maxsize,": "self.InsertStringItem(self.GetItemCount(),",
}

CHECKBOX_ANCHOR = """        CheckListCtrlMixin.__init__(self)
        self.parent = parent
"""
CHECKBOX_REPLACEMENT = """        CheckListCtrlMixin.__init__(self)
        if 'phoenix' in wx.PlatformInfo:
            self.EnableCheckBoxes(True)
        self.parent = parent
"""
CHECKBOX_MARKER = """        if 'phoenix' in wx.PlatformInfo:
            self.EnableCheckBoxes(True)
"""


def main() -> int:
    source = TARGET.read_text(encoding=ENCODING)
    updated = source

    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)

    if CHECKBOX_MARKER not in updated:
        count = updated.count(CHECKBOX_ANCHOR)
        if count != 1:
            raise RuntimeError(f"ancre checkbox absente ou ambiguë: count={count}")
        updated = updated.replace(CHECKBOX_ANCHOR, CHECKBOX_REPLACEMENT, 1)

    forbidden = ("six.MAXSIZE", "InsertItem(sys.maxsize,", "InsertStringItem(sys.maxsize,")
    for token in forbidden:
        if token in updated:
            raise RuntimeError(f"usage incompatible restant dans {TARGET.name}: {token}")

    if updated.count(CHECKBOX_MARKER) != 1:
        raise RuntimeError("activation checkbox Phoenix absente ou dupliquée")
    if "InsertItem(self.GetItemCount()," not in updated:
        raise RuntimeError("index de fin de liste Phoenix absent")

    compile(updated, str(TARGET), "exec")
    if updated == source:
        print("La liste des champs contrat est déjà corrigée")
        return 0

    TARGET.write_text(updated, encoding=ENCODING)
    print("Liste des champs contrat corrigée pour Phoenix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
