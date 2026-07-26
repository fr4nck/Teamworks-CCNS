#!/usr/bin/env python3
"""Report executable six.PY2/six.PY3 attribute usages in Teamworks sources."""

from __future__ import annotations

import argparse
import ast
import io
import tokenize
from pathlib import Path


def read_source(path: Path) -> str:
    data = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    return data.decode(encoding)


def find_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(read_source(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "six"
                and node.attr in {"PY2", "PY3"}
            ):
                violations.append(f"{path}:{node.lineno}: six.{node.attr}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
    parser.add_argument("--output", type=Path, default=Path("six-runtime-branches.txt"))
    args = parser.parse_args()

    violations = find_violations(args.path)
    body = "\n".join(violations)
    if body:
        body += "\n"
    args.output.write_text(body, encoding="utf-8")
    print(f"six_runtime_branches={len(violations)}")
    for violation in violations:
        print(violation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
