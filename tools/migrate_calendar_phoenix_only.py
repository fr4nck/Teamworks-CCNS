#!/usr/bin/env python3
"""Remove obsolete wxPython Classic branches from CTRL_Calendrier_tw.py."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path

TARGET = Path("teamworks/Ctrl/CTRL_Calendrier_tw.py")
REPLACEMENTS = [
    (
        """    def DoDrawing(self, dc):\n        dc.RemoveAll()\n        if 'phoenix' not in wx.PlatformInfo:\n            dc.BeginDrawing()\n        self.caseSurvol = None\n        self.Calendrier(dc)\n        if 'phoenix' not in wx.PlatformInfo:\n            dc.EndDrawing()\n""",
        """    def DoDrawing(self, dc):\n        dc.RemoveAll()\n        self.caseSurvol = None\n        self.Calendrier(dc)\n""",
    ),
    (
        """        if 'phoenix' in wx.PlatformInfo:\n            largeur, hauteur = self.GetClientSize()\n        else:\n            largeur, hauteur = self.GetClientSize()\n""",
        """        largeur, hauteur = self.GetClientSize()\n""",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    path = args.root / TARGET
    with tokenize.open(path) as stream:
        source = stream.read()
        encoding = stream.encoding

    changes = 0
    for old, new in REPLACEMENTS:
        count = source.count(old)
        if count not in (0, 1):
            raise SystemExit(f"Unexpected match count for {path}: {count}")
        if count:
            source = source.replace(old, new)
            changes += 1

    if changes and args.write:
        path.write_text(source, encoding=encoding, newline="")

    print(f"calendar_phoenix_changes={changes}")
    if args.check and changes:
        raise SystemExit(f"{changes} obsolete calendar compatibility blocks remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
