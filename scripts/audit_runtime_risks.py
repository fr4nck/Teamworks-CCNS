#!/usr/bin/env python3
"""Static audit of legacy runtime risks in Teamworks-CCNS.

The audit is read-only and intentionally conservative. It reports risk indicators
without claiming that every match is a defect.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

PYTHON_ROOTS = ("teamworks", "application", "domain", "infrastructure")
PYTHON2_REMOVED_BUILTINS = frozenset(
    {"basestring", "unicode", "long", "xrange", "raw_input"}
)


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    line: int
    detail: str


def iter_python_files(root: Path):
    for dirname in PYTHON_ROOTS:
        base = root / dirname
        if base.exists():
            yield from sorted(base.rglob("*.py"))


def source_lines(path: Path) -> list[str]:
    raw = path.read_bytes()
    for encoding in ("utf-8", "iso-8859-15", "cp1252"):
        try:
            return raw.decode(encoding).splitlines()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").splitlines()


def audit_text(root: Path, path: Path, lines: list[str]) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    findings: list[Finding] = []
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.match(r"except\s*:\s*$", stripped):
            findings.append(Finding("bare-except", rel, number, stripped))
        if "GestionDB.DB(" in line:
            findings.append(Finding("gestiondb-open", rel, number, stripped))
        if "sqlite3.connect(" in line:
            findings.append(Finding("sqlite-direct", rel, number, stripped))
            if re.search(r"sqlite3\.connect\([^\n]*\.encode\(\s*['\"]utf-8['\"]\s*\)", line):
                findings.append(
                    Finding(
                        "sqlite-bytes-path",
                        rel,
                        number,
                        "SQLite path encoded to bytes; keep filesystem paths as str on Python 3",
                    )
                )
        if re.search(r"\b(eval|exec)\s*\(", line) or "__import__(" in line:
            findings.append(Finding("dynamic-execution", rel, number, stripped))
        if re.search(r"open\([^\n]*[\"'](?:w|a|x)b?[\"']", line):
            findings.append(Finding("file-write", rel, number, stripped))
    return findings


def module_bound_names(tree: ast.AST) -> set[str]:
    """Return names explicitly provided by the module itself.

    Compatibility aliases such as ``basestring = str`` are therefore not
    reported as missing Python 2 builtins when they are later referenced.
    """
    bound: set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for child in ast.walk(target):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                        bound.add(child.id)
    return bound


def audit_ast(root: Path, path: Path, lines: list[str]) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    text = "\n".join(lines) + "\n"
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        return [Finding("syntax-unparsed", rel, exc.lineno or 0, exc.msg)]

    findings: list[Finding] = []
    provided_names = module_bound_names(tree)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in PYTHON2_REMOVED_BUILTINS
            and node.id not in provided_names
        ):
            findings.append(
                Finding(
                    "python2-removed-builtin",
                    rel,
                    node.lineno,
                    f"{node.id} is unavailable on Python 3",
                )
            )

    for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        methods = {
            node.name
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for node in ast.walk(class_node):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "Bind"):
                continue
            if len(node.args) < 2:
                continue
            handler = node.args[1]
            if (
                isinstance(handler, ast.Attribute)
                and isinstance(handler.value, ast.Name)
                and handler.value.id == "self"
                and handler.attr not in methods
            ):
                findings.append(
                    Finding(
                        "missing-bound-handler",
                        rel,
                        node.lineno,
                        f"{class_node.name}.{handler.attr}",
                    )
                )
    return findings


def run(root: Path) -> dict:
    findings: list[Finding] = []
    files = list(iter_python_files(root))
    for path in files:
        lines = source_lines(path)
        findings.extend(audit_text(root, path, lines))
        findings.extend(audit_ast(root, path, lines))

    counts = Counter(item.category for item in findings)
    top_files = Counter(item.path for item in findings).most_common(25)
    return {
        "root": str(root),
        "python_files": len(files),
        "counts": dict(sorted(counts.items())),
        "top_files": top_files,
        "findings": [asdict(item) for item in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--fail-on-missing-handlers", action="store_true")
    parser.add_argument("--fail-on-sqlite-bytes-paths", action="store_true")
    parser.add_argument("--fail-on-python2-builtins", action="store_true")
    args = parser.parse_args()

    result = run(Path(args.root).resolve())
    print(f"Python files audited: {result['python_files']}")
    for category, count in result["counts"].items():
        print(f"{category}: {count}")
    print("Top files:")
    for path, count in result["top_files"][:10]:
        print(f"  {count:4d}  {path}")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    missing = result["counts"].get("missing-bound-handler", 0)
    sqlite_bytes = result["counts"].get("sqlite-bytes-path", 0)
    python2_builtins = result["counts"].get("python2-removed-builtin", 0)
    if args.fail_on_missing_handlers and missing:
        return 1
    if args.fail_on_sqlite_bytes_paths and sqlite_bytes:
        return 1
    if args.fail_on_python2_builtins and python2_builtins:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
