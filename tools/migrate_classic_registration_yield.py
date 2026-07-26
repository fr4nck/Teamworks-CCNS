#!/usr/bin/env python3
"""Remove the wxPython Classic-only Yield call from registration validation."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path


TARGET = Path("teamworks/Dlg/DLG_Enregistrement.py")
BLOCK = """        if 'phoenix' not in wx.PlatformInfo:\n            wx.Yield()\n        \n"""


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
    count = source.count(BLOCK)
    if count not in (0, 1):
        raise SystemExit(f"Unexpected match count in {TARGET}: {count}")
    if count and args.write:
        path.write_text(source.replace(BLOCK, ""), encoding=encoding, newline="")

    print(f"classic_registration_yield_blocks={count}")
    if args.check and count:
        raise SystemExit("Classic registration Yield block remains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
