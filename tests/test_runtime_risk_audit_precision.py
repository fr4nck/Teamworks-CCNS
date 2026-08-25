from __future__ import annotations

import ast
from pathlib import Path

from scripts import audit_runtime_risks

ROOT = Path(__file__).resolve().parents[1]


def _expr(source: str):
    return ast.parse(source, mode="eval").body


def test_int_wrapped_width_expression_is_not_reported_as_float():
    assert not audit_runtime_risks.contains_float_width_risk(
        _expr("max(100, int(largeur * 0.22))")
    )
    assert not audit_runtime_risks.contains_float_width_risk(_expr("int(largeur / 2)"))


def test_unwrapped_float_width_expression_remains_detected():
    assert audit_runtime_risks.contains_float_width_risk(_expr("largeur / 2"))
    assert audit_runtime_risks.contains_float_width_risk(_expr("largeur * 0.22"))


def test_sqlite_connect_paths_are_never_encoded_to_bytes():
    findings = []
    for path in sorted((ROOT / "teamworks").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "connect" or not node.args:
                continue
            if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "sqlite3"):
                continue
            first = node.args[0]
            if isinstance(first, ast.Call) and isinstance(first.func, ast.Attribute) and first.func.attr == "encode":
                findings.append((path.relative_to(ROOT).as_posix(), node.lineno))
    assert findings == []
