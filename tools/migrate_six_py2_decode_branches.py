#!/usr/bin/env python3
"""Remove dead Python 2-only decode branches across the legacy source tree."""

from __future__ import annotations

import argparse
import re
import tokenize
from pathlib import Path


PATTERN = re.compile(
    r'(?m)^(?P<indent>[ \t]*)if six\.PY2:\s*\n'
    r'(?P=indent)[ \t]+(?P<name>[A-Za-z_]\w*)\s*=\s*(?P=name)\.decode\((?P<encoding>[^\n]+)\)\s*\n'
)


def iter_python_files(root: Path):
    yield from root.rglob("*.py")


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def write_source(path: Path, source: str, encoding: str) -> None:
    path.write_text(source, encoding=encoding, newline="")


def migrate_file(path: Path, write: bool) -> int:
    source, encoding = read_source(path)
    migrated, count = PATTERN.subn("", source)
    if count and write:
        write_source(path, migrated, encoding)
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total = 0
    changed_files = []
    for path in iter_python_files(args.path):
        count = migrate_file(path, write=args.write)
        if count:
            total += count
            changed_files.append((path, count))

    for path, count in changed_files:
        print(f"{path}: {count}")
    print(f"obsolete_decode_branches={total}")

    if args.check and total:
        raise SystemExit(f"{total} obsolete six.PY2 decode branches remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
