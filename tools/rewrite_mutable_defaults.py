#!/usr/bin/env python3
"""Remplace les paramètres mutables par None dans des fichiers explicitement ciblés."""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

ENCODINGS = ("utf-8", "iso-8859-15", "cp1252")


def read_source(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", raw, 0, 1, f"Encodage non reconnu: {path}")


def empty_factory(node: ast.AST) -> str | None:
    if isinstance(node, ast.List):
        return "[]"
    if isinstance(node, ast.Dict):
        return "{}"
    if isinstance(node, ast.Set):
        return "set()"
    return None


def rewrite(path: Path) -> int:
    source, encoding = read_source(path)
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    replacements: list[tuple[int, int, int]] = []
    insertions: dict[int, list[tuple[str, str]]] = defaultdict(list)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        positional = [*node.args.posonlyargs, *node.args.args]
        offset = len(positional) - len(node.args.defaults)
        pairs = [
            (arg, default)
            for index, arg in enumerate(positional)
            if index >= offset
            for default in [node.args.defaults[index - offset]]
        ]
        pairs.extend(
            (arg, default)
            for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults)
            if default is not None
        )

        init_line = node.body[0].lineno - 1
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            init_line = node.body[0].end_lineno

        indent = " " * (node.col_offset + 4)
        for arg, default in pairs:
            factory = empty_factory(default)
            if factory is None or not hasattr(default, "end_col_offset"):
                continue
            replacements.append((default.lineno - 1, default.col_offset, default.end_col_offset))
            insertions[init_line].append((arg.arg, factory))

    for line_index, start, end in sorted(replacements, reverse=True):
        lines[line_index] = lines[line_index][:start] + "None" + lines[line_index][end:]

    for line_index in sorted(insertions, reverse=True):
        indent = " " * (len(lines[line_index]) - len(lines[line_index].lstrip())) if line_index < len(lines) else "    "
        block = []
        seen = set()
        for name, factory in insertions[line_index]:
            if name in seen:
                continue
            seen.add(name)
            block.extend([
                f"{indent}if {name} is None:\n",
                f"{indent}    {name} = {factory}\n",
            ])
        lines[line_index:line_index] = block

    if replacements:
        path.write_bytes("".join(lines).encode(encoding))
    return len(replacements)


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: rewrite_mutable_defaults.py <fichier> [...]", file=sys.stderr)
        return 2
    total = 0
    for item in argv:
        path = Path(item)
        count = rewrite(path)
        total += count
        print(f"{path}: {count} correction(s)")
    print(f"Total: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
