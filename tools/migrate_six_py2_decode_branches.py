#!/usr/bin/env python3
"""Remove isolated Python 2-only decode branches across the legacy tree."""

from __future__ import annotations

import argparse
import re
import tokenize
from pathlib import Path


IF_PATTERN = re.compile(r"^(?P<indent>[ \t]*)if six\.PY2:\s*$")
DECODE_PATTERN = re.compile(
    r"^(?P<indent>[ \t]+)(?P<name>[A-Za-z_]\w*)\s*=\s*"
    r"(?P=name)\.decode\([^\n]+\)\s*$"
)


def iter_python_files(root: Path):
    yield from root.rglob("*.py")


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def write_source(path: Path, source: str, encoding: str) -> None:
    path.write_text(source, encoding=encoding, newline="")


def indentation_width(value: str) -> int:
    return len(value.expandtabs(8))


def migrate_source(source: str) -> tuple[str, int]:
    """Remove only a six.PY2 block containing exactly one decode assignment."""
    lines = source.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    count = 0

    while index < len(lines):
        if_match = IF_PATTERN.match(lines[index].rstrip("\r\n"))
        if not if_match or index + 1 >= len(lines):
            output.append(lines[index])
            index += 1
            continue

        decode_match = DECODE_PATTERN.match(lines[index + 1].rstrip("\r\n"))
        if not decode_match:
            output.append(lines[index])
            index += 1
            continue

        parent_width = indentation_width(if_match.group("indent"))
        body_width = indentation_width(decode_match.group("indent"))
        if body_width <= parent_width:
            output.append(lines[index])
            index += 1
            continue

        next_index = index + 2
        if next_index < len(lines):
            next_line = lines[next_index].rstrip("\r\n")
            if next_line.strip():
                next_indent = next_line[: len(next_line) - len(next_line.lstrip(" \t"))]
                if indentation_width(next_indent) > parent_width:
                    # The branch contains more than one statement: leave it untouched.
                    output.append(lines[index])
                    index += 1
                    continue

        index += 2
        count += 1

    return "".join(output), count


def migrate_file(path: Path, write: bool) -> int:
    source, encoding = read_source(path)
    migrated, count = migrate_source(source)
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
