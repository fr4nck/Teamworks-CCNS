import ast
from pathlib import Path


TEAMWORKS_ROOT = Path("teamworks")
FORBIDDEN_METHODS = {"InsertStringItem", "SetStringItem"}


def iter_python_sources():
    yield from sorted(TEAMWORKS_ROOT.rglob("*.py"))


def test_completed_python3_and_wx_migrations_do_not_regress():
    findings = []

    for source_path in iter_python_sources():
        source = source_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(source_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "raw_input":
                    findings.append(f"{source_path}:{node.lineno}: raw_input")

            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in FORBIDDEN_METHODS:
                    findings.append(
                        f"{source_path}:{node.lineno}: {node.func.attr}"
                    )

    assert findings == [], "Anciennes API réintroduites:\n" + "\n".join(findings)
