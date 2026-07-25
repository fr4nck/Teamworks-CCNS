#!/usr/bin/env python3
"""Remove standalone ``import six`` statements when no six symbol remains."""

from __future__ import annotations

import argparse
import re
import tokenize
from pathlib import Path


IMPORT_PATTERN = re.compile(r"(?m)^import six[ \t]*\n")
SIX_REFERENCE_PATTERN = re.compile(r"\bsix\b")


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate_file(path: Path, write: bool) -> bool:
    source, encoding = read_source(path)
    without_import, count = IMPORT_PATTERN.subn("", source, count=1)
    if count == 0 or SIX_REFERENCE_PATTERN.search(without_import):
        return False
    if write:
        path.write_text(without_import, encoding=encoding, newline="")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    changed = []
    for path in args.path.rglob("*.py"):
        if migrate_file(path, write=args.write):
            changed.append(path)

    for path in changed:
        print(path)
    print(f"unused_six_imports={len(changed)}")

    if args.check and changed:
        raise SystemExit(f"{len(changed)} unused six imports remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
