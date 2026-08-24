#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit statique des risques susceptibles de casser une RC Teamworks-CCNS.

Le rapport couvre tout ``teamworks/``. Les catégories larges restent informatives ;
le contrôle ``wx-staticbox-parent`` est volontairement à haute confiance et peut
servir de garde-fou CI.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import tokenize
from collections import defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS = ROOT / "teamworks"

TEXT_PATTERNS = (
    ("dynamic-eval", "high", re.compile(r"\beval\s*\(")),
    ("dynamic-exec", "high", re.compile(r"\bexec\s*\(")),
    ("bare-except", "medium", re.compile(r"^\s*except\s*:\s*(?:#.*)?$")),
    ("silent-exception", "medium", re.compile(r"except(?:\s+Exception)?\s*:\s*(?:#.*)?$")),
    ("todo-marker", "low", re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b", re.IGNORECASE)),
    ("not-implemented", "high", re.compile(r"\bNotImplementedError\b")),
    ("assert-runtime", "medium", re.compile(r"^\s*assert\s+")),
    ("sql-select-star", "medium", re.compile(r"SELECT\s+\*\s+FROM\b", re.IGNORECASE)),
    ("sql-insert-values-no-columns", "high", re.compile(r"INSERT\s+INTO\s+[A-Za-z0-9_]+\s+VALUES\s*\(", re.IGNORECASE)),
    ("mysql55-add-column-if-not-exists", "high", re.compile(r"ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS", re.IGNORECASE)),
    ("shell-true", "high", re.compile(r"shell\s*=\s*True")),
    ("sys-path-mutation", "medium", re.compile(r"sys\.path\.(?:append|insert)\s*\(")),
    ("wx-yield", "medium", re.compile(r"\bwx\.Yield\s*\(")),
    ("wx-fixed-size", "medium", re.compile(r"\b(?:size|pos)\s*=\s*\(\s*-?\d+\s*,\s*-?\d+\s*\)")),
    ("wx-literal-min-size", "medium", re.compile(r"\.SetMinSize\(\s*\(\s*-?\d+\s*,\s*-?\d+")),
    ("wx-grandparent-chain", "medium", re.compile(r"\.GetGrandParent\(\)(?:\.Get(?:Grand)?Parent\(\))+")),
)


def iter_python_files(root: Path = TEAMWORKS) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        name = path.name.lower()
        if ".bak" in name or name.endswith("~"):
            continue
        yield path


def decode_source(path: Path) -> str:
    with path.open("rb") as stream:
        encoding, _ = tokenize.detect_encoding(stream.readline)
    return path.read_bytes().decode(encoding, errors="replace")


def expr_key(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def call_name(node: ast.AST) -> str:
    if not isinstance(node, ast.Call):
        return ""
    return expr_key(node.func)


def assignment_targets(node: ast.AST) -> list[str]:
    targets: list[ast.AST] = []
    if isinstance(node, ast.Assign):
        targets.extend(node.targets)
    elif isinstance(node, ast.AnnAssign):
        targets.append(node.target)
    names: list[str] = []
    for target in targets:
        if isinstance(target, (ast.Name, ast.Attribute)):
            key = expr_key(target)
            if key:
                names.append(key)
    return names


def _is_orientation(node: ast.AST) -> bool:
    key = expr_key(node)
    return key in {"wx.VERTICAL", "wx.HORIZONTAL"}


def _staticbox_spec(call: ast.Call) -> tuple[str, str] | None:
    """Retourne (parent_externe, parent_attendu) pour wx.StaticBoxSizer."""
    if call_name(call) != "wx.StaticBoxSizer" or not call.args:
        return None
    args = call.args
    # Phoenix : wx.StaticBoxSizer(orient, parent, label)
    if _is_orientation(args[0]) and len(args) >= 2:
        return expr_key(args[1]), "@GET_STATIC_BOX@"
    # Variante : wx.StaticBoxSizer(static_box, orient)
    return "", expr_key(args[0])


def _first_parent(call: ast.Call) -> str:
    return expr_key(call.args[0]) if call.args else ""


def _scope_staticbox_findings(path: Path, scope: ast.AST) -> list[dict[str, object]]:
    sizers: dict[str, dict[str, object]] = {}
    sizer_edges: dict[str, set[str]] = defaultdict(set)
    sizer_widgets: dict[str, list[tuple[str, int]]] = defaultdict(list)
    widget_parents: dict[str, tuple[str, int]] = {}

    nodes = list(ast.walk(scope))
    for node in nodes:
        value = None
        if isinstance(node, ast.Assign):
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            value = node.value
        if not isinstance(value, ast.Call):
            continue
        targets = assignment_targets(node)
        if not targets:
            continue
        callee = call_name(value)
        for target in targets:
            spec = _staticbox_spec(value)
            if spec is not None:
                outer_parent, expected = spec
                sizers[target] = {
                    "outer_parent": outer_parent,
                    "expected_parent": expected,
                    "line": getattr(node, "lineno", 0),
                }
                continue
            if callee.endswith("Sizer") or callee.startswith("wx.") and callee.split(".")[-1].endswith("Sizer"):
                sizers.setdefault(target, {"outer_parent": "", "expected_parent": "", "line": getattr(node, "lineno", 0)})
                continue
            if value.args:
                widget_parents[target] = (_first_parent(value), getattr(node, "lineno", 0))

    for node in nodes:
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"Add", "Insert", "Prepend"} or not node.args:
            continue
        owner = expr_key(node.func.value)
        child = node.args[0]
        child_key = expr_key(child)
        if owner not in sizers:
            continue
        if child_key in sizers:
            sizer_edges[owner].add(child_key)
        elif isinstance(child, ast.Call):
            parent = _first_parent(child)
            pseudo = f"<inline@{getattr(child, 'lineno', 0)}>"
            widget_parents[pseudo] = (parent, getattr(child, "lineno", 0))
            sizer_widgets[owner].append((pseudo, getattr(child, "lineno", 0)))
        elif child_key:
            sizer_widgets[owner].append((child_key, getattr(node, "lineno", 0)))

    findings: list[dict[str, object]] = []
    relpath = path.relative_to(ROOT).as_posix()
    for root_sizer, info in sizers.items():
        outer_parent = str(info.get("outer_parent") or "")
        if not outer_parent:
            continue
        descendants = {root_sizer}
        stack = [root_sizer]
        while stack:
            current = stack.pop()
            for child_sizer in sizer_edges.get(current, set()):
                if child_sizer not in descendants:
                    descendants.add(child_sizer)
                    stack.append(child_sizer)
        for sizer in descendants:
            for widget, add_line in sizer_widgets.get(sizer, []):
                parent_info = widget_parents.get(widget)
                if not parent_info:
                    continue
                parent, create_line = parent_info
                if parent != outer_parent:
                    continue
                findings.append(
                    {
                        "file": relpath,
                        "line": create_line or add_line,
                        "code": "wx-staticbox-parent",
                        "severity": "critical",
                        "sizer": root_sizer,
                        "widget": widget,
                        "actual_parent": parent,
                        "expected_parent": f"{root_sizer}.GetStaticBox()",
                    }
                )
    return findings


def staticbox_parent_findings(path: Path, source: str) -> list[dict[str, object]]:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [{
            "file": path.relative_to(ROOT).as_posix(),
            "line": exc.lineno or 0,
            "code": "parse-error",
            "severity": "critical",
            "detail": exc.msg,
        }]

    findings: list[dict[str, object]] = []
    # Analyse chaque fonction/méthode séparément pour éviter les collisions de noms.
    scopes = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not scopes:
        scopes = [tree]
    for scope in scopes:
        findings.extend(_scope_staticbox_findings(path, scope))
    # Déduplication stable.
    unique: dict[tuple[object, ...], dict[str, object]] = {}
    for finding in findings:
        key = (
            finding.get("file"), finding.get("line"), finding.get("code"),
            finding.get("sizer"), finding.get("widget"),
        )
        unique[key] = finding
    return sorted(unique.values(), key=lambda item: (str(item.get("file")), int(item.get("line", 0))))


def text_findings(path: Path, source: str) -> list[dict[str, object]]:
    relpath = path.relative_to(ROOT).as_posix()
    findings: list[dict[str, object]] = []
    for lineno, line in enumerate(source.splitlines(), 1):
        for code, severity, regex in TEXT_PATTERNS:
            if regex.search(line):
                findings.append({
                    "file": relpath,
                    "line": lineno,
                    "code": code,
                    "severity": severity,
                    "text": line.strip()[:240],
                })
    return findings


def audit(root: Path = TEAMWORKS) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    scanned = 0
    for path in sorted(iter_python_files(root)):
        scanned += 1
        source = decode_source(path)
        findings.extend(staticbox_parent_findings(path, source))
        findings.extend(text_findings(path, source))

    by_code: dict[str, int] = defaultdict(int)
    by_file: dict[str, int] = defaultdict(int)
    for finding in findings:
        by_code[str(finding["code"])] += 1
        by_file[str(finding["file"])] += 1

    blockers = [f for f in findings if f["code"] in {"wx-staticbox-parent", "parse-error", "mysql55-add-column-if-not-exists", "sql-insert-values-no-columns"}]
    return {
        "scanned_files": scanned,
        "finding_count": len(findings),
        "blocker_count": len(blockers),
        "by_code": dict(sorted(by_code.items())),
        "by_file": dict(sorted(by_file.items(), key=lambda item: (-item[1], item[0]))),
        "blockers": blockers,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit pré-RC de Teamworks-CCNS")
    parser.add_argument("--json", dest="json_path", default="", help="Écrit le rapport JSON dans ce fichier")
    parser.add_argument("--fail-on-staticbox", action="store_true")
    parser.add_argument("--fail-on-blockers", action="store_true")
    args = parser.parse_args(argv)

    report = audit()
    print(f"Fichiers Python scannés : {report['scanned_files']}")
    print(f"Occurrences recensées : {report['finding_count']}")
    print(f"Bloqueurs à haute confiance : {report['blocker_count']}")
    for code, count in report["by_code"].items():
        print(f"{count:5d}  {code}")
    if report["blockers"]:
        print("\nBloqueurs :")
        for item in report["blockers"]:
            print(f"- {item['file']}:{item['line']} [{item['code']}] {item.get('widget') or item.get('text') or item.get('detail', '')}")

    if args.json_path:
        Path(args.json_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.fail_on_staticbox and any(item["code"] == "wx-staticbox-parent" for item in report["findings"]):
        return 1
    if args.fail_on_blockers and report["blocker_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
