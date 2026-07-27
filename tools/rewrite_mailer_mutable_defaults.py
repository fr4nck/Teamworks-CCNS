#!/usr/bin/env python3
"""Sécurise les paramètres mutables de DLG_Mailer sans modifier son API observable."""

from __future__ import annotations

import ast
from pathlib import Path

TARGETS = {
    "SetDonnees": "donnees",
    "Envoyer": "listeDestinataires",
    "VerifieFusion": "listeDestinataires",
    "SetPiecesJointes": "listeFichiers",
}


def read_source(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8", "iso-8859-15", "cp1252"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", raw, 0, 1, "Encodage non reconnu")


def _is_none_guard(node: ast.stmt, target: str) -> bool:
    if not isinstance(node, ast.If) or len(node.body) != 1:
        return False
    test = node.test
    if not (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == target
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Is)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
    ):
        return False
    assignment = node.body[0]
    return (
        isinstance(assignment, ast.Assign)
        and len(assignment.targets) == 1
        and isinstance(assignment.targets[0], ast.Name)
        and assignment.targets[0].id == target
        and isinstance(assignment.value, ast.List)
        and not assignment.value.elts
    )


def _is_docstring(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def rewrite(path: Path) -> int:
    source, encoding = read_source(path)
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    default_edits: list[tuple[int, int, int, str]] = []
    guard_moves: list[tuple[int, int, int]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        target = TARGETS.get(node.name)
        if target is None:
            continue

        # Préserve la docstring comme première instruction de la fonction.
        if len(node.body) >= 2 and _is_none_guard(node.body[0], target) and _is_docstring(node.body[1]):
            guard_moves.append((node.body[0].lineno - 1, node.body[0].end_lineno, node.body[1].end_lineno))

        args = node.args.args
        defaults = node.args.defaults
        default_offset = len(args) - len(defaults)
        for index, arg in enumerate(args):
            if arg.arg != target or index < default_offset:
                continue
            default = defaults[index - default_offset]
            if not isinstance(default, ast.List) or default.elts:
                continue
            if ast.get_source_segment(source, default) != "[]":
                continue

            indent = " " * (node.col_offset + 4)
            init = f"{indent}if {target} is None:\n{indent}    {target} = []\n"
            body_line = node.body[0].end_lineno if _is_docstring(node.body[0]) else node.body[0].lineno - 1
            default_edits.append((default.lineno - 1, default.col_offset, body_line, init))
            break

    changes = 0
    for start, end, insert_after in sorted(guard_moves, reverse=True):
        guard = lines[start:end]
        del lines[start:end]
        adjusted_insert = insert_after - (end - start)
        lines[adjusted_insert:adjusted_insert] = guard
        changes += 1

    for default_line, column, body_line, init in sorted(default_edits, reverse=True):
        lines[default_line] = lines[default_line][:column] + "None" + lines[default_line][column + 2 :]
        lines[body_line:body_line] = [init]
        changes += 1

    if changes:
        path.write_bytes("".join(lines).encode(encoding))
    return changes


if __name__ == "__main__":
    target = Path("teamworks/Dlg/DLG_Mailer.py")
    print(f"{target}: {rewrite(target)} correction(s)")
