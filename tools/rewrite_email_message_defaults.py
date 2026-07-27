#!/usr/bin/env python3
"""Sécurise les valeurs par défaut mutables de UTILS_Envoi_email.Message."""

from __future__ import annotations

import ast
from pathlib import Path

TARGETS = ("destinataires", "fichiers", "images", "champs")


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
    message_init = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "__init__"
        and isinstance(getattr(node, "parent", None), type(None))
        and any(arg.arg == "destinataires" for arg in node.args.args)
    )

    args = message_init.args.args
    defaults = message_init.args.defaults
    offset = len(args) - len(defaults)
    edits: list[tuple[int, int]] = []
    initializers: list[str] = []

    for index, arg in enumerate(args):
        if arg.arg not in TARGETS or index < offset:
            continue
        default = defaults[index - offset]
        if isinstance(default, (ast.List, ast.Dict)) and not getattr(default, "elts", None) and not getattr(default, "keys", None):
            edits.append((default.lineno - 1, default.col_offset))
            empty = "{}" if arg.arg == "champs" else "[]"
            initializers.append(f"        if {arg.arg} is None:\n            {arg.arg} = {empty}\n")

    for line_index, column in sorted(edits, reverse=True):
        old = "{}" if lines[line_index][column:column + 2] == "{}" else "[]"
        lines[line_index] = lines[line_index][:column] + "None" + lines[line_index][column + len(old):]

    if initializers:
        body_line = message_init.body[0].lineno - 1
        lines[body_line:body_line] = initializers

    if edits:
        path.write_bytes("".join(lines).encode(encoding))
    return len(edits)


if __name__ == "__main__":
    target = Path("teamworks/Utils/UTILS_Envoi_email.py")
    print(f"{target}: {rewrite(target)} correction(s)")
