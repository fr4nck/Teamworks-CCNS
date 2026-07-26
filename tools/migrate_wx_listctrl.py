#!/usr/bin/env python3
"""Migration prudente des anciens appels wx.ListCtrl.

Par défaut, le script analyse le dépôt et affiche les remplacements sûrs.
L'option --write applique uniquement les transformations exactes suivantes :

- InsertStringItem(index, label) -> InsertItem(index, label)
- six.MAXSIZE -> sys.maxsize

Aucune transformation n'est appliquée lorsqu'une ligne est ambiguë.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path("teamworks")
INSERT_PATTERN = re.compile(r"\.InsertStringItem\(")
MAXSIZE_PATTERN = re.compile(r"\bsix\.MAXSIZE\b")


def migrate_source(source: str) -> tuple[str, int]:
    migrated = INSERT_PATTERN.sub(".InsertItem(", source)
    replacements = migrated.count(".InsertItem(") - source.count(".InsertItem(")

    maxsize_count = len(MAXSIZE_PATTERN.findall(migrated))
    if maxsize_count:
        migrated = MAXSIZE_PATTERN.sub("sys.maxsize", migrated)
        replacements += maxsize_count

        if "import sys" not in migrated:
            lines = migrated.splitlines()
            insert_at = 0
            while insert_at < len(lines) and (
                lines[insert_at].startswith("#!")
                or "coding:" in lines[insert_at]
                or lines[insert_at].startswith("#")
                or not lines[insert_at].strip()
            ):
                insert_at += 1
            lines.insert(insert_at, "import sys")
            migrated = "\n".join(lines)
            if source.endswith("\n"):
                migrated += "\n"

    return migrated, replacements


def iter_python_files(root: Path):
    yield from sorted(root.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    total = 0
    for path in iter_python_files(args.root):
        source = path.read_text(encoding="utf-8", errors="replace")
        migrated, count = migrate_source(source)
        if not count:
            continue

        total += count
        print(f"{path}: {count} remplacement(s)")
        if args.write:
            path.write_text(migrated, encoding="utf-8", newline="\n")

    print(f"Total: {total} remplacement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
