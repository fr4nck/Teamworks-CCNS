#!/usr/bin/env python3
"""Replace exact six.MAXSIZE references with sys.maxsize while preserving encoding."""

from __future__ import annotations

import argparse
import io
import re
import tokenize
from pathlib import Path

PATTERN = re.compile(r"\bsix\.MAXSIZE\b")


def read_source(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding), encoding


def ensure_sys_import(source: str) -> str:
    if re.search(r"^\s*import\s+sys(?:\s|,|$)", source, re.MULTILINE):
        return source
    lines = source.splitlines(keepends=True)
    insert_at = 0
    while insert_at < len(lines):
        stripped = lines[insert_at].strip()
        if (
            insert_at < 2
            and (lines[insert_at].startswith("#!") or "coding:" in lines[insert_at])
        ) or not stripped or stripped.startswith("#"):
            insert_at += 1
            continue
        break
    newline = "\r\n" if "\r\n" in source else "\n"
    lines.insert(insert_at, f"import sys{newline}")
    return "".join(lines)


def migrate_source(source: str) -> tuple[str, int]:
    migrated, count = PATTERN.subn("sys.maxsize", source)
    if count:
        migrated = ensure_sys_import(migrated)
    return migrated, count


def iter_python_files(path: Path):
    if path.is_file():
        if path.suffix == ".py":
            yield path
        return
    yield from sorted(path.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
