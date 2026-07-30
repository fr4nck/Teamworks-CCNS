#!/usr/bin/env python3
"""Inventorie les paramètres mutables dans les fonctions Python du dépôt."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ENCODINGS = ("utf-8",)
MUTABLE_NODES = (ast.List, ast.Dict, ast.Set)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    function: str
    parameter: str
    kind: str


def read_source(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", raw, 0, 1, f"Encodage non reconnu: {path}")


def find_mutable_defaults(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(read_source(path))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            positional = [*node.args.posonlyargs, *node.args.args]
            offset = len(positional) - len(node.args.defaults)
            for index, default in enumerate(node.args.defaults):
                if isinstance(default, MUTABLE_NODES):
                    parameter = positional[offset + index].arg
                    findings.append(
                        Finding(path, default.lineno, node.name, parameter, type(default).__name__)
                    )
            for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
                if isinstance(default, MUTABLE_NODES):
                    findings.append(
                        Finding(path, default.lineno, node.name, arg.arg, type(default).__name__)
                    )
    return findings


def format_findings(findings: Iterable[Finding]) -> str:
    return "\n".join(
        f"{item.path}:{item.line}:{item.function}:{item.parameter}:{item.kind}"
        for item in findings
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("teamworks"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    findings = find_mutable_defaults(args.root)
    if findings:
        print(format_findings(findings))
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
