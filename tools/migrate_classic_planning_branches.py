#!/usr/bin/env python3
"""Remove wxPython Classic-only branches from the planning control."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path


TARGET = Path("teamworks/Ctrl/CTRL_Planning.py")
REPLACEMENTS = {
    """        if 'phoenix' not in wx.PlatformInfo:\n            dc.BeginDrawing()\n""": "",
    """        if 'phoenix' not in wx.PlatformInfo:\n            dc.EndDrawing()\n""": "",
    """        if 'phoenix' in wx.PlatformInfo:\n            r.Offset(-(xView*xDelta),-(yView*yDelta))\n        else :\n            r.OffsetXY(-(xView*xDelta),-(yView*yDelta))\n""": """        r.Offset(-(xView*xDelta),-(yView*yDelta))\n""",
    """        if 'phoenix' in wx.PlatformInfo:\n            tailleDC = self.GetSize()[0]-20,  self.GetSize()[1]\n        else:\n            tailleDC = self.GetSizeTuple()[0] - 20, self.GetSizeTuple()[1]\n""": """        tailleDC = self.GetSize()[0]-20, self.GetSize()[1]\n""",
}


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    path = args.root / TARGET
    source, encoding = read_source(path)
    total = 0
    for old, new in REPLACEMENTS.items():
        count = source.count(old)
        if old.startswith("        if 'phoenix' not"):
            if count not in (0, 2):
                raise SystemExit(f"Unexpected repeated planning match count: {count}")
        elif count not in (0, 1):
            raise SystemExit(f"Unexpected planning match count: {count}")
        if count:
            source = source.replace(old, new)
            total += count

    if total and args.write:
        path.write_text(source, encoding=encoding, newline="")

    print(f"classic_planning_blocks={total}")
    if args.check and total:
        raise SystemExit(f"{total} classic planning blocks remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
