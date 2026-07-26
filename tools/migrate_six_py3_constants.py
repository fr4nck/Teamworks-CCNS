#!/usr/bin/env python3
"""Apply small, deterministic Python 3 runtime cleanups."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path

TOKEN = "six.PY3"
REPLACEMENT = "True"
EXPORT_TYPE_CHECK = 'type(valeur) not in ("str", "unicode")'
EXPORT_TYPE_REPLACEMENT = "not isinstance(valeur, str)"


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def migrate_file(path: Path, write: bool) -> int:
    source, encoding = read_source(path)
    changed = 0

    six_count = source.count(TOKEN)
    if six_count:
        source = source.replace(TOKEN, REPLACEMENT)
        changed += six_count

    if path.as_posix().endswith("teamworks/Utils/UTILS_Export.py"):
        export_count = source.count(EXPORT_TYPE_CHECK)
        if export_count not in (0, 1):
            raise SystemExit(f"Unexpected export type-check count in {path}: {export_count}")
        if export_count:
            source = source.replace(EXPORT_TYPE_CHECK, EXPORT_TYPE_REPLACEMENT)
            changed += export_count

    if changed and write:
        path.write_text(source, encoding=encoding, newline="")
    return changed


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

    print(f"pending_runtime_cleanups={total}")
    print(f"files={files}")
    if args.check and total:
        raise SystemExit(f"{total} Python 3 runtime cleanups remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
