#!/usr/bin/env python3
"""Remove dead wxPython Classic branches from the photo editor."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path

TARGET = Path("teamworks/Dlg/DLG_Editeur_photo.py")
REPLACEMENTS = {
    """    if 'phoenix' in wx.PlatformInfo:\n        imagewx = wx.Image(image.size[0], image.size[1])\n    else:\n        imagewx = wx.Image(image.size[0], image.size[1])\n""": """    imagewx = wx.Image(image.size[0], image.size[1])\n""",
    """        if 'phoenix' in wx.PlatformInfo:\n            largeurDC, hauteurDC = self.GetClientSize()\n        else:\n            largeurDC, hauteurDC = self.GetClientSize()\n""": """        largeurDC, hauteurDC = self.GetClientSize()\n""",
    """        if 'phoenix' in wx.PlatformInfo:\n            self.largeurDC, self.hauteurDC = self.GetClientSize()\n        else:\n            self.largeurDC, self.hauteurDC = self.GetClientSize()\n""": """        self.largeurDC, self.hauteurDC = self.GetClientSize()\n""",
    """        if 'phoenix' in wx.PlatformInfo:\n            self._Buffer = wx.Bitmap(self.largeurDC, self.hauteurDC)\n        else:\n            self._Buffer = wx.Bitmap(self.largeurDC, self.hauteurDC)\n""": """        self._Buffer = wx.Bitmap(self.largeurDC, self.hauteurDC)\n""",
    """        if 'phoenix' in wx.PlatformInfo:\n            self.bmp = wx.Bitmap(source)\n        else:\n            self.bmp = wx.Bitmap(source)\n""": """        self.bmp = wx.Bitmap(source)\n""",
    """        if 'phoenix' not in wx.PlatformInfo:\n            dc.BeginDrawing()\n""": "",
    """        if 'phoenix' not in wx.PlatformInfo:\n            dc.EndDrawing()\n""": "",
}


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate(path: Path, write: bool) -> int:
    source, encoding = read_source(path)
    total = 0
    for old, new in REPLACEMENTS.items():
        count = source.count(old)
        if count:
            source = source.replace(old, new)
            total += count
    if total and write:
        path.write_text(source, encoding=encoding, newline="")
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    count = migrate(args.root / TARGET, args.write)
    print(f"photo_editor_phoenix_blocks={count}")
    if args.check and count:
        raise SystemExit(f"{count} photo editor Phoenix cleanup blocks remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
