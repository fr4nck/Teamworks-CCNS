#!/usr/bin/env python3
"""Inventorie les branches Phoenix dont les deux chemins sont identiques."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_ROOT = Path("teamworks")
ENCODINGS = ("utf-8",)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int


def _is_phoenix_test(node: ast.AST) -> bool:
    try:
        return "phoenix" in ast.unparse(node).lower()
    except Exception:
        return False


def _same_body(left: list[ast.stmt], right: list[ast.stmt]) -> bool:
    left_module = ast.Module(body=left, type_ignores=[])
    right_module = ast.Module(body=right, type_ignores=[])
    return ast.dump(left_module, include_attributes=False) == ast.dump(
        right_module,
        include_attributes=False,
    )


def _read_source(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", raw, 0, 1, f"Encodage non reconnu: {path}")


def find_redundant_phoenix_branches(root: Path = DEFAULT_ROOT) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(_read_source(path))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.If) or not node.orelse:
                continue
            if _is_phoenix_test(node.test) and _same_body(node.body, node.orelse):
                findings.append(Finding(path=path, line=node.lineno))
    return findings


def format_findings(findings: Iterable[Finding]) -> str:
    return "\n".join(f"{item.path.as_posix()}:{item.line}" for item in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="retourne un code non nul lorsqu'une redondance est détectée",
    )
    args = parser.parse_args()

    findings = find_redundant_phoenix_branches(args.root)
    if findings:
        print(format_findings(findings))
    if args.check and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
