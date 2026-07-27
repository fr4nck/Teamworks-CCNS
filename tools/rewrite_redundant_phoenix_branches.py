#!/usr/bin/env python3
"""Supprime des branches Phoenix/classique strictement identiques.

Le script travaille uniquement sur les chemins explicitement fournis. Il conserve
l'encodage source et remplace chaque if/else redondant par le corps commun.
"""

from __future__ import annotations

import ast
import sys
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


def is_phoenix_test(node: ast.AST) -> bool:
    return "phoenix" in ast.unparse(node).lower()


def same_statements(left: list[ast.stmt], right: list[ast.stmt]) -> bool:
    return ast.dump(ast.Module(body=left, type_ignores=[]), include_attributes=False) == ast.dump(
        ast.Module(body=right, type_ignores=[]), include_attributes=False
    )


def rewrite(path: Path) -> int:
    source, encoding = read_source(path)
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    candidates: list[ast.If] = []

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.If)
            and node.orelse
            and is_phoenix_test(node.test)
            and same_statements(node.body, node.orelse)
            and hasattr(node, "end_lineno")
        ):
            candidates.append(node)

    for node in sorted(candidates, key=lambda item: item.lineno, reverse=True):
        start = node.lineno - 1
        end = node.end_lineno
        first_body_line = node.body[0].lineno - 1
        last_body_line = node.body[-1].end_lineno
        indent = len(lines[start]) - len(lines[start].lstrip())
        body_indent = len(lines[first_body_line]) - len(lines[first_body_line].lstrip())
        remove_indent = max(0, body_indent - indent)
        replacement = []
        for line in lines[first_body_line:last_body_line]:
            replacement.append(line[remove_indent:] if line.strip() else line)
        lines[start:end] = replacement

    if candidates:
        path.write_bytes("".join(lines).encode(encoding))
    return len(candidates)


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: rewrite_redundant_phoenix_branches.py <fichier> [...]", file=sys.stderr)
        return 2
    total = 0
    for item in argv:
        path = Path(item)
        count = rewrite(path)
        total += count
        print(f"{path}: {count} branche(s) simplifiée(s)")
    print(f"Total: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
