from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "teamworks"
LEGACY_TYPE_NAMES = {"str", "unicode", "long", "int", "float", "bytes"}


def _string_constants(node: ast.AST) -> set[str]:
    values: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.add(child.value)
    return values


def test_runtime_types_are_not_compared_with_string_names() -> None:
    violations: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            import tokenize

            with tokenize.open(path) as stream:
                source = stream.read()
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left, *node.comparators]
            has_type_call = any(
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Name)
                and item.func.id == "type"
                for item in operands
            )
            names = set().union(*(_string_constants(item) for item in operands))
            if has_type_call and names & LEGACY_TYPE_NAMES:
                violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")

    assert not violations, "String-based runtime type comparisons found:\n" + "\n".join(violations)
