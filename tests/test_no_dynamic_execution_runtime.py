from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_teamworks_contains_no_direct_dynamic_execution():
    findings = []
    for path in sorted((ROOT / "teamworks").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id not in {"eval", "exec", "__import__"}:
                continue
            findings.append((path.relative_to(ROOT).as_posix(), node.lineno, node.func.id))
    assert findings == []
