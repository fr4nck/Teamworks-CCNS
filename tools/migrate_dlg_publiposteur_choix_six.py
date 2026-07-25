#!/usr/bin/env python3
"""Remove the remaining ``six.text_type`` dependency from DLG_Publiposteur_Choix."""

from __future__ import annotations

import argparse
from pathlib import Path
import tokenize


TARGET = Path("teamworks/Dlg/DLG_Publiposteur_Choix.py")
REPLACEMENTS = (
    ("# -*- coding: iso-8859-15 -*-", "# -*- coding: utf-8 -*-"),
    ("import six\n", ""),
    ("six.text_type(donnees[0])", "str(donnees[0])"),
    ("six.text_type(donnees[x])", "str(donnees[x])"),
)


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate_source(source: str) -> tuple[str, int]:
    migrated = source
    changes = 0
    for old, new in REPLACEMENTS:
        count = migrated.count(old)
        if count not in (0, 1):
            raise ValueError(f"unexpected occurrence count for {old!r}: {count}")
        if count:
            migrated = migrated.replace(old, new, 1)
            changes += 1
    return migrated, changes


def migrate_file(path: Path, write: bool) -> int:
    source, encoding = read_source(path)
    migrated, changes = migrate_source(source)
    if write and changes:
        path.write_text(migrated, encoding="utf-8", newline="")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TARGET)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    changes = migrate_file(args.path, write=args.write)
    print(f"pending_changes={changes}")
    if args.check and changes:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
