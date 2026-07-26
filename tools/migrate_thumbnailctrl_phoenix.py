#!/usr/bin/env python3
"""Remove wxPython Classic drawing fallbacks from CTRL_thumbnailctrl.py."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path

TARGET = Path("teamworks/Ctrl/CTRL_thumbnailctrl.py")
REPLACEMENTS = {
    "        if 'phoenix' not in wx.PlatformInfo:\n            dc.BeginDrawing()\n        \n": "",
    "                if 'phoenix' in wx.PlatformInfo:\n                    dc.DrawRoundedRectangle(dotrect, 2)\n                else:\n                    dc.DrawRoundedRectangleRect(dotrect, 2)\n": "                dc.DrawRoundedRectangle(dotrect, 2)\n",
    "        if 'phoenix' not in wx.PlatformInfo:\n            dc.EndDrawing()\n": "",
}


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate(path: Path, write: bool) -> int:
    source, encoding = read_source(path)
    total = 0
    for old, new in REPLACEMENTS.items():
        count = source.count(old)
        if count not in (0, 1):
            raise SystemExit(f"Unexpected match count for {old!r}: {count}")
        if count:
            total += count
            source = source.replace(old, new)
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
    print(f"thumbnailctrl_classic_blocks={count}")
    if args.check and count:
        raise SystemExit(f"{count} thumbnailctrl Classic blocks remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
