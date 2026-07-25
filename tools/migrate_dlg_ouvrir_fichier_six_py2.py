#!/usr/bin/env python3
"""Remove the dead Python 2 filename decoding branch from DLG_Ouvrir_fichier."""

from __future__ import annotations

import argparse
from pathlib import Path

TARGET = Path("teamworks/Dlg/DLG_Ouvrir_fichier.py")
OLD = """            if six.PY2:\n                nomFichier = nomFichier.decode(\"iso-8859-15\")\n"""


def migrate(path: Path, write: bool) -> int:
    source = path.read_text(encoding="utf-8")
    count = source.count(OLD)
    if count not in (0, 1):
        raise SystemExit(f"Unexpected six.PY2 branch count in {path}: {count}")
    if count == 0:
        return 0
    migrated = source.replace(OLD, "", 1)
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
        raise SystemExit(f"{changed} obsolete six.PY2 branch remains in {args.path}")
    print(f"obsolete_branches={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
