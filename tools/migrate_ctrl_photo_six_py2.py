#!/usr/bin/env python3
"""Remove the two dead Python 2 decoding branches from CTRL_Photo."""

from __future__ import annotations

import argparse
from pathlib import Path


TARGET = Path("teamworks/Ctrl/CTRL_Photo.py")
OLD = """            if six.PY2:\n                nomCadre = nomCadre.decode(\"iso-8859-15\")\n"""


def migrate(path: Path, write: bool) -> int:
    source = path.read_text(encoding="utf-8", errors="strict")
    count = source.count(OLD)
    if count not in (0, 2):
        raise SystemExit(f"Unexpected six.PY2 branch count in {path}: {count}")
    if count == 0:
        return 0
    migrated = source.replace(OLD, "")
    if write:
        path.write_text(migrated, encoding="utf-8")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TARGET)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    changed = migrate(args.path, write=args.write)
    if args.check and changed:
        raise SystemExit(f"{changed} obsolete six.PY2 branches remain in {args.path}")
    print(f"obsolete_branches={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
