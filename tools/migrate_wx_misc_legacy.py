#!/usr/bin/env python3
"""Migrate straightforward wxPython Classic APIs while preserving source encodings."""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import tokenize


REPLACEMENTS = {
    ".GetClientSizeTuple(": ".GetClientSize(",
    "wx.BitmapFromImage(": "wx.Bitmap(",
    "wx.ImageFromStream(": "wx.Image(",
    "wx.PySimpleApp(": "wx.App(",
    ".SetToolTipString(": ".SetToolTip(",
    "wx.OPEN": "wx.FD_OPEN",
    "wx.PyValidator": "wx.Validator",
}


def read_source(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding), encoding


def migrate_source(source: str) -> tuple[str, int]:
    migrated = source
    total = 0
    for old, new in REPLACEMENTS.items():
        count = migrated.count(old)
        if count:
            migrated = migrated.replace(old, new)
            total += count
    return migrated, total


def iter_python_files(path: Path):
    if path.is_file():
        if path.suffix == ".py":
            yield path
        return
    yield from sorted(path.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
    args = parser.parse_args()

    total = 0
    for path in iter_python_files(args.path):
        source, encoding = read_source(path)
        migrated, count = migrate_source(source)
        if not count:
            continue
        total += count
        print(f"{path}: {count} remplacement(s)")
        if args.write:
            path.write_bytes(migrated.encode(encoding))

    print(f"Total: {total} remplacement(s)")
    return 1 if args.check and total else 0


if __name__ == "__main__":
    raise SystemExit(main())
