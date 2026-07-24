#!/usr/bin/env python3
"""Migrate exact wx.NewId() calls to wx.NewIdRef() while preserving encoding."""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import re
import tokenize

ROOT = Path("teamworks")
PATTERN = re.compile(r"\bwx\.NewId\(\)")


def read_source(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding), encoding


def migrate_source(source: str) -> tuple[str, int]:
    return PATTERN.subn("wx.NewIdRef()", source)


def iter_python_files(path: Path):
    if path.is_file():
        if path.suffix == ".py":
            yield path
        return
    yield from sorted(path.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--path", type=Path, default=ROOT)
    args = parser.parse_args()

    total = 0
    for path in iter_python_files(args.path):
        source, encoding = read_source(path)
        migrated, count = migrate_source(source)
        if not count:
            continue
        total += count
        print(f"{path}: {count} remplacement(s)")
        if args.write:
            path.write_bytes(migrated.encode(encoding))

    print(f"Total: {total} remplacement(s)")
    if args.check and total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
