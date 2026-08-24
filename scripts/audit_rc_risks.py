#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit statique des risques susceptibles de casser une RC Teamworks-CCNS.

Le rapport couvre tout ``teamworks/``. Les catégories larges servent d'inventaire ;
les bloqueurs sont volontairement limités à des règles structurelles à haute
confiance afin de ne pas confondre dette historique, commentaire et défaut actif.
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

# Inventaire textuel : utile pour prioriser les fouilles, mais non bloquant à lui seul.
TEXT_PATTERNS = (
    ("dynamic-eval", "high", re.compile(r"\beval\s*\(")),
    ("dynamic-exec", "high", re.compile(r"\bexec\s*\(")),
    ("bare-except", "medium", re.compile(r"^\s*except\s*:\s*(?:#.*)?$")),
    ("silent-exception", "medium", re.compile(r"except(?:\s+Exception)?\s*:\s*(?:#.*)?$")),
    ("todo-marker", "low", re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b", re.IGNORECASE)),
    ("not-implemented", "high", re.compile(r"\bNotImplementedError\b")),
    ("assert-runtime", "medium", re.compile(r"^\s*assert\s+")),
    ("shell-true", "high", re.compile(r"shell\s*=\s*True")),
    ("sys-path-mutation", "medium", re.compile(r"sys\.path\.(?:append|insert)\s*\(")),
    ("wx-yield", "medium", re.compile(r"\bwx\.Yield\s*\(")),
    ("wx-fixed-size", "medium", re.compile(r"\b(?:size|pos)\s*=\s*\(\s*-?\d+\s*,\s*-?\d+\s*\)")),
    ("wx-literal-min-size", "medium", re.compile(r"\.SetMinSize\(\s*\(\s*-?\d+\s*,\s*-?\d+")),
    ("wx-grandparent-chain", "medium", re.compile(r"\.GetGrandParent\(\)(?:\.Get(?:Grand)?Parent\(\))+")),
)

# SQL : analysé uniquement dans de vraies constantes Python, hors docstrings.
SQL_PATTERNS = (
    ("sql-select-star", "medium", re.compile(r"SELECT\s+\*\s+FROM\b", re.IGNORECASE)),
    (
        "sql-insert-values-no-columns",
        "critical",
        re.compile(r"INSERT\s+INTO\s+[A-Za-z0-9_]+\s+VALUES\s*\(", re.IGNORECASE),
    ),
    (
        "mysql55-add-column-if-not-exists",
        "critical",
        re.compile(r"ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS", re.IGNORECASE),
    ),
)

BLOCKER_CODES = {
    "parse-error",
    "wx-staticbox-parent",
    "wx-staticbox-helper-parent",
    "mysql55-add-column-if-not-exists",
    "sql-insert-values-no-columns",
}


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
    return expr_key(node) in {"wx.VERTICAL", "wx.HORIZONTAL"}


def _first_parent(call: ast.Call) -> str:
    return expr_key(call.args[0]) if call.args else ""


def _looks_like_widget_constructor(call: ast.Call) -> bool:
    """Écarte les appels utilitaires comme ``getattr(...)`` passés à ``Add``.

    Les constructeurs wx sont explicites. Les contrôles maison historiques ont
    généralement un nom de classe commençant par une majuscule (``CTRL(...)``,
    ``MyDatePickerCtrl(...)``). Un appel fonctionnel en minuscules ne doit pas
    être interprété comme la création inline d'un enfant wx.
    """
    callee = call_name(call)
    if not callee:
        return False
    leaf = callee.split(".")[-1]
    if leaf.endswith("Sizer"):
        return False
    if callee.startswith("wx."):
        return True
    return bool(leaf[:1].isupper())


def _descendant_sizers(root_sizer: str, edges: dict[str, set[str]]) -> set[str]:
    descendants = {root_sizer}
    stack = [root_sizer]
    while stack:
        current = stack.pop()
        for child in edges.get(current, set()):
            if child not in descendants:
                descendants.add(child)
                stack.append(child)
    return descendants


def _scope_staticbox_findings(path: Path, scope: ast.AST) -> list[dict[str, object]]:
    """Détecte parentages directs et helpers alimentant un StaticBoxSizer.

    Exemple indirect couvert : ``self._row(page, grid, ...)`` lorsque ``grid``
    est contenu dans un StaticBoxSizer créé avec ``page``. Le helper reçoit alors
    le mauvais parent, même si les wx.StaticText/TextCtrl sont créés ailleurs.
    """
    sizers: dict[str, dict[str, object]] = {}
    static_boxes: dict[str, tuple[str, int]] = {}
    sizer_edges: dict[str, set[str]] = defaultdict(set)
    sizer_widgets: dict[str, list[tuple[str, int]]] = defaultdict(list)
    widget_parents: dict[str, tuple[str, int]] = {}

    nodes = list(ast.walk(scope))

    # Premier passage : objets nommés et leurs parents.
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
            if callee == "wx.StaticBox" and value.args:
                static_boxes[target] = (_first_parent(value), getattr(node, "lineno", 0))
                continue

            if callee == "wx.StaticBoxSizer" and value.args:
                outer_parent = ""
                if _is_orientation(value.args[0]) and len(value.args) >= 2:
                    # Phoenix : wx.StaticBoxSizer(orient, parent, label)
                    outer_parent = expr_key(value.args[1])
                else:
                    # wx.StaticBoxSizer(static_box, orient)
                    first = value.args[0]
                    if isinstance(first, ast.Call) and call_name(first) == "wx.StaticBox":
                        outer_parent = _first_parent(first)
                    else:
                        outer_parent = static_boxes.get(expr_key(first), ("", 0))[0]
                sizers[target] = {
                    "outer_parent": outer_parent,
                    "is_staticbox": True,
                    "line": getattr(node, "lineno", 0),
                }
                continue

            if callee.endswith("Sizer") or (
                callee.startswith("wx.") and callee.split(".")[-1].endswith("Sizer")
            ):
                sizers.setdefault(
                    target,
                    {"outer_parent": "", "is_staticbox": False, "line": getattr(node, "lineno", 0)},
                )
                continue

            # Une variable ajoutée ensuite à un sizer : mémoriser son parent wx.
            if value.args:
                widget_parents[target] = (_first_parent(value), getattr(node, "lineno", 0))

    # Deuxième passage : graphe des sizers et widgets ajoutés.
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
        elif isinstance(child, ast.Call) and _looks_like_widget_constructor(child):
            pseudo = f"<inline@{getattr(child, 'lineno', 0)}>"
            widget_parents[pseudo] = (_first_parent(child), getattr(child, "lineno", 0))
            sizer_widgets[owner].append((pseudo, getattr(child, "lineno", 0)))
        elif not isinstance(child, ast.Call) and child_key:
            sizer_widgets[owner].append((child_key, getattr(node, "lineno", 0)))

    relpath = path.relative_to(ROOT).as_posix()
    findings: list[dict[str, object]] = []

    for root_sizer, info in sizers.items():
        if not info.get("is_staticbox"):
            continue
        outer_parent = str(info.get("outer_parent") or "")
        if not outer_parent:
            continue
        descendants = _descendant_sizers(root_sizer, sizer_edges)

        # Cas direct : un contrôle appartenant au sous-arbre du sizer est créé
        # avec le panel extérieur au lieu du StaticBox.
        for sizer in descendants:
            for widget, add_line in sizer_widgets.get(sizer, []):
                parent_info = widget_parents.get(widget)
                if not parent_info:
                    continue
                parent, create_line = parent_info
                if parent == outer_parent:
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

        # Cas indirect : un helper reçoit à la fois le panel extérieur et un
        # sizer descendant. C'est le pattern classique _row(page, grid, ...).
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            callee = call_name(node)
            if not callee or callee.startswith("wx."):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"Add", "Insert", "Prepend"}:
                continue
            arg_keys = [expr_key(arg) for arg in node.args]
            if outer_parent not in arg_keys:
                continue
            matching_sizers = [s for s in descendants if s != root_sizer and s in arg_keys]
            if not matching_sizers:
                continue
            # Restreint aux helpers privés/de construction pour éviter de bloquer
            # sur des appels métier qui transporteraient ces objets par hasard.
            helper_leaf = callee.split(".")[-1].lower()
            if not (
                helper_leaf.startswith("_")
                or "row" in helper_leaf
                or "ligne" in helper_leaf
                or "field" in helper_leaf
                or "champ" in helper_leaf
            ):
                continue
            findings.append(
                {
                    "file": relpath,
                    "line": getattr(node, "lineno", 0),
                    "code": "wx-staticbox-helper-parent",
                    "severity": "critical",
                    "sizer": root_sizer,
                    "helper": callee,
                    "actual_parent": outer_parent,
                    "descendant_sizer": matching_sizers[0],
                    "expected_parent": f"{root_sizer}.GetStaticBox()",
                }
            )

    return findings


def _parse_tree(path: Path, source: str) -> tuple[ast.AST | None, list[dict[str, object]]]:
    try:
        return ast.parse(source, filename=str(path)), []
    except SyntaxError as exc:
        return None, [{
            "file": path.relative_to(ROOT).as_posix(),
            "line": exc.lineno or 0,
            "code": "parse-error",
            "severity": "critical",
            "detail": exc.msg,
        }]


def staticbox_parent_findings(path: Path, tree: ast.AST) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    scopes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if not scopes:
        scopes = [tree]
    for scope in scopes:
        findings.extend(_scope_staticbox_findings(path, scope))

    unique: dict[tuple[object, ...], dict[str, object]] = {}
    for finding in findings:
        key = (
            finding.get("file"),
            finding.get("line"),
            finding.get("code"),
            finding.get("sizer"),
            finding.get("widget"),
            finding.get("helper"),
        )
        unique[key] = finding
    return sorted(
        unique.values(),
        key=lambda item: (str(item.get("file")), int(item.get("line", 0))),
    )


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Identifiants AST des constantes utilisées comme docstrings."""
    result: set[int] = set()
    candidates = [tree] + [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for owner in candidates:
        body = getattr(owner, "body", None)
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            result.add(id(first.value))
    return result


def sql_findings(path: Path, tree: ast.AST) -> list[dict[str, object]]:
    """Scanne le SQL réellement stocké dans le code, jamais les docstrings."""
    relpath = path.relative_to(ROOT).as_posix()
    docs = _docstring_nodes(tree)
    findings: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docs
        ):
            continue
        value = node.value
        for code, severity, regex in SQL_PATTERNS:
            match = regex.search(value)
            if not match:
                continue
            findings.append(
                {
                    "file": relpath,
                    "line": getattr(node, "lineno", 0),
                    "code": code,
                    "severity": severity,
                    "text": match.group(0)[:240],
                }
            )
    return findings


def text_findings(path: Path, source: str) -> list[dict[str, object]]:
    relpath = path.relative_to(ROOT).as_posix()
    findings: list[dict[str, object]] = []
    for lineno, line in enumerate(source.splitlines(), 1):
        for code, severity, regex in TEXT_PATTERNS:
            if regex.search(line):
                findings.append(
                    {
                        "file": relpath,
                        "line": lineno,
                        "code": code,
                        "severity": severity,
                        "text": line.strip()[:240],
                    }
                )
    return findings


def audit(root: Path = TEAMWORKS) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    scanned = 0
    for path in sorted(iter_python_files(root)):
        scanned += 1
        source = decode_source(path)
        tree, parse_findings = _parse_tree(path, source)
        findings.extend(parse_findings)
        if tree is not None:
            findings.extend(staticbox_parent_findings(path, tree))
            findings.extend(sql_findings(path, tree))
        findings.extend(text_findings(path, source))

    by_code: dict[str, int] = defaultdict(int)
    by_file: dict[str, int] = defaultdict(int)
    for finding in findings:
        by_code[str(finding["code"])] += 1
        by_file[str(finding["file"])] += 1

    blockers = [f for f in findings if f["code"] in BLOCKER_CODES]
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
    parser.add_argument(
        "--json",
        dest="json_path",
        default="",
        help="Écrit le rapport JSON dans ce fichier",
    )
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
            detail = item.get("widget") or item.get("helper") or item.get("text") or item.get("detail", "")
            print(f"- {item['file']}:{item['line']} [{item['code']}] {detail}")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.fail_on_staticbox and any(
        str(item["code"]).startswith("wx-staticbox") for item in report["findings"]
    ):
        return 1
    if args.fail_on_blockers and report["blocker_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
