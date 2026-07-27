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
    changes = 0

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

            line_index = default.lineno - 1
            segment = ast.get_source_segment(source, default)
            if segment != "[]":
                continue
            column = default.col_offset
            lines[line_index] = lines[line_index][:column] + "None" + lines[line_index][column + 2 :]

            body_line = node.body[0].lineno - 1
            indent = " " * (node.col_offset + 4)
            init = f"{indent}if {target} is None:\n{indent}    {target} = []\n"
            lines[body_line:body_line] = [init]
            changes += 1
            break

    if changes:
        path.write_bytes("".join(lines).encode(encoding))
    return changes


if __name__ == "__main__":
    target = Path("teamworks/Dlg/DLG_Mailer.py")
    print(f"{target}: {rewrite(target)} correction(s)")
