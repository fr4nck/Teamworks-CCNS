#!/usr/bin/env python3
"""Sécurise tous les CheckListCtrlMixin historiques pour wxPython Phoenix."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"
ENCODING = "iso-8859-15"
MIXIN_PATTERN = re.compile(r"(?m)^(?P<indent>[ \t]*)CheckListCtrlMixin\.__init__\(self\)[ \t]*$")
FORBIDDEN = (
    "InsertItem(six.MAXSIZE,",
    "InsertItem(sys.maxsize,",
    "InsertStringItem(six.MAXSIZE,",
    "InsertStringItem(sys.maxsize,",
)
REPLACEMENTS = {
    "InsertItem(six.MAXSIZE,": "InsertItem(self.GetItemCount(),",
    "InsertItem(sys.maxsize,": "InsertItem(self.GetItemCount(),",
    "InsertStringItem(six.MAXSIZE,": "InsertStringItem(self.GetItemCount(),",
    "InsertStringItem(sys.maxsize,": "InsertStringItem(self.GetItemCount(),",
}


def enable_native_checkboxes(source: str, path: Path) -> str:
    matches = list(MIXIN_PATTERN.finditer(source))
    if not matches:
        return source

    chunks: list[str] = []
    cursor = 0
    for match in matches:
        chunks.append(source[cursor:match.end()])
        indent = match.group("indent")
        following = source[match.end():match.end() + 220]
        marker = f"{indent}if 'phoenix' in wx.PlatformInfo:\n{indent}    self.EnableCheckBoxes(True)"
        if marker not in following:
            chunks.append(
                f"\n{indent}if 'phoenix' in wx.PlatformInfo:"
                f"\n{indent}    self.EnableCheckBoxes(True)"
            )
        cursor = match.end()
    chunks.append(source[cursor:])
    updated = "".join(chunks)

    if updated.count("self.EnableCheckBoxes(True)") < len(matches):
        raise RuntimeError(f"cases Phoenix manquantes dans {path}")
    return updated


def correct(path: Path) -> bool:
    source = path.read_text(encoding=ENCODING)
    if "CheckListCtrlMixin.__init__(self)" not in source:
        return False

    updated = source
    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)
    updated = enable_native_checkboxes(updated, path)

    for token in FORBIDDEN:
        if token in updated:
            raise RuntimeError(f"index incompatible restant dans {path}: {token}")

    mixin_count = len(MIXIN_PATTERN.findall(updated))
    checkbox_count = updated.count("self.EnableCheckBoxes(True)")
    if checkbox_count < mixin_count:
        raise RuntimeError(
            f"activation Phoenix insuffisante dans {path}: "
            f"mixin={mixin_count}, checkboxes={checkbox_count}"
        )

    compile(updated, str(path), "exec")
    if updated == source:
        return False
    path.write_text(updated, encoding=ENCODING)
    return True


def main() -> int:
    candidates = sorted(TEAMWORKS.rglob("*.py"))
    changed: list[Path] = []
    checked: list[Path] = []
    for path in candidates:
        source = path.read_text(encoding=ENCODING)
        if "CheckListCtrlMixin.__init__(self)" not in source:
            continue
        checked.append(path)
        if correct(path):
            changed.append(path)

    if len(checked) < 10:
        raise RuntimeError(f"inventaire CheckListCtrlMixin anormalement court: {len(checked)}")

    print(f"Contrôles vérifiés : {len(checked)}")
    for path in checked:
        print(f"  - {path.relative_to(ROOT)}")
    print(f"Contrôles modifiés : {len(changed)}")
    for path in changed:
        print(f"  - {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
