#!/usr/bin/env python3
"""Migre les anciens constructeurs d'images wxPython Classic vers Phoenix.

Par défaut, le script analyse les fichiers Python sous ``teamworks`` sans les
modifier. L'option ``--write`` applique uniquement les transformations exactes
suivantes :

- ``wx.EmptyBitmap(...)`` -> ``wx.Bitmap(...)``
- ``wx.EmptyImage(...)`` -> ``wx.Image(...)``
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path("teamworks")
PATTERNS = (
    (re.compile(r"\bwx\.EmptyBitmap\("), "wx.Bitmap("),
    (re.compile(r"\bwx\.EmptyImage\("), "wx.Image("),
)


def migrate_source(source: str) -> tuple[str, int]:
    migrated = source
    total = 0

    for pattern, replacement in PATTERNS:
        migrated, count = pattern.subn(replacement, migrated)
        total += count

    return migrated, total


def iter_python_files(root: Path):
    if root.is_file():
        yield root
    else:
        yield from sorted(root.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--path", type=Path, default=ROOT)
    args = parser.parse_args()

    total = 0
    for path in iter_python_files(args.path):
        source = path.read_text(encoding="utf-8", errors="replace")
        migrated, count = migrate_source(source)
        if not count:
            continue

        total += count
        print(f"{path}: {count} remplacement(s)")
        if args.write:
            path.write_text(migrated, encoding="utf-8", newline="\n")

    print(f"Total: {total} remplacement(s)")
    if args.check and total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
