#!/usr/bin/env python3
"""Replace executable ``six.PY3`` checks with the definitive Python 3 value."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path

TOKEN = "six.PY3"
REPLACEMENT = "True"


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate_file(path: Path, write: bool) -> int:
    source, encoding = read_source(path)
    count = source.count(TOKEN)
    if count and write:
        path.write_text(source.replace(TOKEN, REPLACEMENT), encoding=encoding, newline="")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total = 0
    files = 0
    for path in sorted(args.path.rglob("*.py")):
        count = migrate_file(path, write=args.write)
        if count:
            print(f"{path}: {count}")
            total += count
            files += 1

    print(f"six_py3_occurrences={total}")
    print(f"files={files}")
    if args.check and total:
        raise SystemExit(f"{total} six.PY3 occurrences remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
