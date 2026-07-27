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


def rewrite(path: Path) -> int:
    source, encoding = read_source(path)
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    edits: list[tuple[int, int, int, str, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        target = TARGETS.get(node.name)
        if target is None:
            continue

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
            edits.append((default.lineno - 1, default.col_offset, node.body[0].lineno - 1, target, init))
            break

    for default_line, column, body_line, _target, init in sorted(edits, reverse=True):
        lines[default_line] = lines[default_line][:column] + "None" + lines[default_line][column + 2 :]
        lines[body_line:body_line] = [init]

    if edits:
        path.write_bytes("".join(lines).encode(encoding))
    return len(edits)


if __name__ == "__main__":
    target = Path("teamworks/Dlg/DLG_Mailer.py")
    print(f"{target}: {rewrite(target)} correction(s)")
