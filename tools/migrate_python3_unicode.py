#!/usr/bin/env python3
"""Migration prudente des appels ``unicode(...)`` vers ``str(...)``.

Le script fonctionne en analyse seule par défaut. L'option ``--write`` applique
uniquement les appels directs ``unicode(...)`` détectés dans les sources Python.
Les chaînes, commentaires et attributs nommés ``unicode`` ne sont pas modifiés.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


ROOT = Path("teamworks")


class UnicodeCallMigrator(ast.NodeTransformer):
    """Remplace uniquement les appels directs à la fonction Python 2 unicode."""

    def __init__(self) -> None:
        self.replacements = 0

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "unicode":
            node.func = ast.copy_location(ast.Name(id="str", ctx=ast.Load()), node.func)
            self.replacements += 1
        return node


def migrate_source(source: str) -> tuple[str, int]:
    tree = ast.parse(source)
    migrator = UnicodeCallMigrator()
    migrated_tree = migrator.visit(tree)
    ast.fix_missing_locations(migrated_tree)

    if not migrator.replacements:
        return source, 0

    migrated = ast.unparse(migrated_tree)
    if source.endswith("\n"):
        migrated += "\n"
    return migrated, migrator.replacements


def iter_python_files(root: Path):
    yield from sorted(root.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    total = 0
    for path in iter_python_files(args.root):
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            migrated, count = migrate_source(source)
        except SyntaxError:
            continue

        if not count:
            continue

        total += count
        print(f"{path}: {count} remplacement(s)")
        if args.write:
            path.write_text(migrated, encoding="utf-8", newline="\n")

    print(f"Total: {total} remplacement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
