#!/usr/bin/env python3
"""Corrige les contrôles de contrat incompatibles avec wxPython Phoenix."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENCODING = "iso-8859-15"
LIST_TARGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p4.py"
SIZER_TARGETS = (
    ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p5.py",
    ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_modele_contrat_p2.py",
)

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
INVALID_BOX_FLAGS = "wx.ALIGN_CENTER_VERTICAL|wx.EXPAND"
VALID_BOX_FLAGS = "wx.EXPAND"


def correct_list() -> bool:
    source = LIST_TARGET.read_text(encoding=ENCODING)
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
            raise RuntimeError(f"usage incompatible restant dans {LIST_TARGET.name}: {token}")

    if updated.count(CHECKBOX_MARKER) != 1:
        raise RuntimeError("activation checkbox Phoenix absente ou dupliquée")
    if "InsertItem(self.GetItemCount()," not in updated:
        raise RuntimeError("index de fin de liste Phoenix absent")

    compile(updated, str(LIST_TARGET), "exec")
    if updated == source:
        return False
    LIST_TARGET.write_text(updated, encoding=ENCODING)
    return True


def correct_sizer(path: Path) -> bool:
    source = path.read_text(encoding=ENCODING)
    updated = source.replace(INVALID_BOX_FLAGS, VALID_BOX_FLAGS)

    if INVALID_BOX_FLAGS in updated:
        raise RuntimeError(f"drapeaux BoxSizer incompatibles restants dans {path.name}")
    if VALID_BOX_FLAGS not in updated:
        raise RuntimeError(f"drapeau wx.EXPAND attendu absent dans {path.name}")

    compile(updated, str(path), "exec")
    if updated == source:
        return False
    path.write_text(updated, encoding=ENCODING)
    return True


def main() -> int:
    changed = []
    if correct_list():
        changed.append(LIST_TARGET.name)
    for path in SIZER_TARGETS:
        if correct_sizer(path):
            changed.append(path.name)

    if changed:
        print("Contrôles contrat corrigés pour Phoenix : " + ", ".join(changed))
    else:
        print("Les contrôles contrat sont déjà corrigés")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
