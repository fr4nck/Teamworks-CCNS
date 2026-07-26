#!/usr/bin/env python3
"""Migrate exact wx.Menu.AppendMenu calls to AppendSubMenu.

Only calls with exactly three positional arguments and no keyword arguments are
rewritten:

    menu.AppendMenu(identifier, label, submenu)
    menu.AppendSubMenu(submenu, label)

The obsolete identifier is intentionally discarded because Phoenix creates and
returns the menu item itself.
"""

from __future__ import annotations

import argparse
import ast
import io
import tokenize
from pathlib import Path


def read_source(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding), encoding


def byte_col_to_char(line: str, byte_col: int) -> int:
    return len(line.encode("utf-8")[:byte_col].decode("utf-8", errors="ignore"))


def absolute_offset(lines: list[str], lineno: int, byte_col: int) -> int:
    prefix = sum(len(line) for line in lines[: lineno - 1])
    return prefix + byte_col_to_char(lines[lineno - 1], byte_col)


def migrate_source(source: str) -> tuple[str, int]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source, 0

    lines = source.splitlines(keepends=True)
    replacements: list[tuple[int, int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "AppendMenu":
            continue
        if len(node.args) != 3 or node.keywords:
            continue
        if not all(hasattr(part, "end_lineno") for part in (node, node.func.value, node.args[1], node.args[2])):
            continue

        receiver = ast.get_source_segment(source, node.func.value)
        label = ast.get_source_segment(source, node.args[1])
        submenu = ast.get_source_segment(source, node.args[2])
        if receiver is None or label is None or submenu is None:
            continue

        start = absolute_offset(lines, node.lineno, node.col_offset)
        end = absolute_offset(lines, node.end_lineno, node.end_col_offset)
        replacements.append((start, end, f"{receiver}.AppendSubMenu({submenu}, {label})"))

    migrated = source
    for start, end, replacement in sorted(replacements, reverse=True):
        migrated = migrated[:start] + replacement + migrated[end:]
    return migrated, len(replacements)


def iter_python_files(path: Path):
    if path.is_file():
        if path.suffix == ".py":
            yield path
        return
    yield from sorted(path.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
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
    return 1 if args.check and total else 0


if __name__ == "__main__":
    raise SystemExit(main())
