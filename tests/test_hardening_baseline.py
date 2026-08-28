from __future__ import annotations

import ast
from pathlib import Path

from scripts.audit_runtime_risks import run as run_runtime_audit


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOTS = ("teamworks", "application", "domain", "infrastructure")
BARE_EXCEPT_CEILING = 214
MUTABLE_DEFAULT_CEILING = 80
MUTABLE_NODES = (ast.List, ast.Dict, ast.Set)


def _python_files(*roots: str):
    for dirname in roots:
        base = ROOT / dirname
        if base.exists():
            yield from sorted(base.rglob("*.py"))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_all_runtime_sources_are_parseable() -> None:
    failures: list[str] = []
    files = list(_python_files(*RUNTIME_ROOTS))
    assert files, "aucune source runtime trouvée"
    for path in files:
        try:
            _parse(path)
        except (OSError, UnicodeError, SyntaxError) as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
    assert not failures, "sources non analysées :\n" + "\n".join(failures)


def test_no_dynamic_execution_in_runtime() -> None:
    findings: list[str] = []
    for path in _python_files(*RUNTIME_ROOTS):
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id in {"eval", "exec"}:
                findings.append(f"{path.relative_to(ROOT)}:{node.lineno}:{node.func.id}")
    assert not findings, "exécution dynamique réintroduite :\n" + "\n".join(findings)


def test_bare_except_debt_does_not_increase() -> None:
    report = run_runtime_audit(ROOT)
    count = report["counts"].get("bare-except", 0)
    assert count <= BARE_EXCEPT_CEILING, (
        f"dette bare except en hausse : {count} > {BARE_EXCEPT_CEILING}"
    )


def test_mutable_default_debt_does_not_increase() -> None:
    count = 0
    for path in _python_files("teamworks"):
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            count += sum(isinstance(default, MUTABLE_NODES) for default in node.args.defaults)
            count += sum(
                isinstance(default, MUTABLE_NODES)
                for default in node.args.kw_defaults
                if default is not None
            )
    assert count <= MUTABLE_DEFAULT_CEILING, (
        f"dette paramètres mutables en hausse : {count} > {MUTABLE_DEFAULT_CEILING}"
    )
