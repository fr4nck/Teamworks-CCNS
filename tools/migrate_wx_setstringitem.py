#!/usr/bin/env python3
"""Migration prudente de wx.ListCtrl.SetStringItem vers SetItem.

Le script analyse les fichiers Python sous ``teamworks``. Par défaut, il
n'écrit rien et affiche les fichiers concernés. L'option ``--write`` applique
uniquement la transformation exacte ``.SetStringItem(`` -> ``.SetItem(``.

L'option ``--path`` permet de limiter l'analyse à un fichier ou un dossier.
L'option ``--check`` renvoie un code de sortie non nul si des appels obsolètes
sont encore détectés, afin de pouvoir intégrer l'audit à la CI.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path("teamworks")
PATTERN = re.compile(r"\.SetStringItem\(")


def migrate_source(source: str) -> tuple[str, int]:
    migrated, count = PATTERN.subn(".SetItem(", source)
    return migrated, count


def iter_python_files(root: Path):
    if root.is_file():
        if root.suffix == ".py":
            yield root
        return

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
