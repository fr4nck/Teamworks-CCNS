#!/usr/bin/env python3
"""Migrate obsolete Python 2 builtin names without touching strings or comments."""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import tokenize


REPLACEMENTS = {
    "xrange": "range",
    "basestring": "str",
    "unicode": "str",
    "long": "int",
}


def detect_source(path: Path) -> tuple[bytes, str, str]:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    newline = "\r\n" if b"\r\n" in data else "\n"
    return data, encoding, newline


def migrate_source(source: str) -> tuple[str, int]:
    tokens = []
    changes = 0
    reader = io.StringIO(source).readline
    for token in tokenize.generate_tokens(reader):
        if token.type == tokenize.NAME and token.string in REPLACEMENTS:
            token = tokenize.TokenInfo(
                token.type,
                REPLACEMENTS[token.string],
                token.start,
                token.end,
                token.line,
            )
            changes += 1
        tokens.append(token)
    return tokenize.untokenize(tokens), changes


def migrate_file(path: Path, write: bool) -> int:
    data, encoding, newline = detect_source(path)
    source = data.decode(encoding)
    migrated, changes = migrate_source(source)
    if not changes:
        return 0
    if newline == "\r\n":
        migrated = migrated.replace("\r\n", "\n").replace("\n", "\r\n")
    if write:
        path.write_bytes(migrated.encode(encoding))
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="teamworks")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.path)
    total = 0
    files = 0
    paths = [root] if root.is_file() else sorted(root.rglob("*.py"))
    for path in paths:
        changes = migrate_file(path, args.write)
        if changes:
            files += 1
            total += changes
            print(f"{path}: {changes}")

    print(f"Python 2 builtin names: {total} occurrence(s) in {files} file(s)")
    if args.check and total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
