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
import warnings
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
    for encoding in ("utf-8",):
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
        if re.search(r"open\([^\n]*[\"'](?:w|a|x)b?[\"']", line):
            findings.append(Finding("file-write", rel, number, stripped))
    return findings


def audit_compile_warnings(root: Path, path: Path, lines: list[str]) -> list[Finding]:
    """Capture Python parser/compiler warnings without executing the module."""
    rel = path.relative_to(root).as_posix()
    text = "\n".join(lines) + "\n"
    findings: list[Finding] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            compile(text, rel, "exec", dont_inherit=True)
        except SyntaxError:
            return findings
    seen: set[tuple[int, str]] = set()
    for warning in caught:
        if not issubclass(warning.category, (SyntaxWarning, DeprecationWarning)):
            continue
        line = int(getattr(warning, "lineno", 0) or 0)
        detail = str(warning.message)
        key = (line, detail)
        if key in seen:
            continue
        seen.add(key)
        findings.append(Finding("python-compile-warning", rel, line, detail))
    return findings


def assigned_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        for child in ast.walk(target):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                names.add(child.id)
    return names


def module_binding_lines(tree: ast.Module) -> dict[str, int]:
    """Return the first module-scope binding line for each name.

    Module-level control-flow blocks are traversed, but function and class bodies
    are excluded because their assignments are local to those scopes.
    """
    bindings: dict[str, int] = {}

    def record(name: str, line: int) -> None:
        bindings[name] = min(bindings.get(name, line), line)

    def visit_statements(statements: list[ast.stmt]) -> None:
        for node in statements:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                record(node.name, node.lineno)
                continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    record(alias.asname or alias.name.split(".", 1)[0], node.lineno)
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                for name in assigned_names(node):
                    record(name, node.lineno)

            nested_blocks = []
            for field in ("body", "orelse", "finalbody"):
                value = getattr(node, field, None)
                if isinstance(value, list):
                    nested_blocks.append(value)
            if isinstance(node, ast.Try):
                nested_blocks.extend(handler.body for handler in node.handlers)
            if isinstance(node, ast.Match):
                nested_blocks.extend(case.body for case in node.cases)
            for block in nested_blocks:
                visit_statements(block)

    visit_statements(tree.body)
    return bindings


def module_name_for_path(root: Path, path: Path) -> str:
    """Return the import name used by Teamworks for a project Python file."""
    rel = path.relative_to(root)
    parts = list(rel.parts)
    if parts and parts[0] == "teamworks":
        parts = parts[1:]
    if not parts:
        return ""
    filename = parts[-1]
    if filename == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(filename).stem
    return ".".join(parts)


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def module_import_aliases(tree: ast.Module, current_module: str) -> dict[str, str]:
    """Map module-scope import aliases to fully qualified project references."""
    aliases: dict[str, str] = {}
    package = current_module.rsplit(".", 1)[0] if "." in current_module else ""

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    root_name = alias.name.split(".", 1)[0]
                    aliases[root_name] = root_name
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package_parts = package.split(".") if package else []
                up = max(0, node.level - 1)
                if up:
                    package_parts = package_parts[:-up] if up <= len(package_parts) else []
                base_parts = package_parts + ([base] if base else [])
                base = ".".join(part for part in base_parts if part)
            for alias in node.names:
                if alias.name == "*":
                    continue
                binding = alias.asname or alias.name
                aliases[binding] = ".".join(part for part in (base, alias.name) if part)
    return aliases


def project_module_path(root: Path, module_name: str) -> Path | None:
    """Resolve a project import name without importing or executing the module."""
    if not module_name:
        return None
    parts = module_name.split(".")
    candidates = [
        root.joinpath(*parts).with_suffix(".py"),
        root.joinpath(*parts, "__init__.py"),
        root.joinpath("teamworks", *parts).with_suffix(".py"),
        root.joinpath("teamworks", *parts, "__init__.py"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resolve_project_base(
    root: Path,
    path: Path,
    tree: ast.Module,
    base: ast.AST,
) -> tuple[Path, str] | None:
    """Resolve a base expression such as CORE.Panel to a project class."""
    raw = dotted_name(base)
    if not raw:
        return None

    current_module = module_name_for_path(root, path)
    aliases = module_import_aliases(tree, current_module)
    first, dot, rest = raw.partition(".")
    if first in aliases:
        expanded = aliases[first]
        if dot:
            expanded = f"{expanded}.{rest}"
    else:
        expanded = raw

    if "." not in expanded:
        module_name = current_module
        class_name = expanded
    else:
        module_name, class_name = expanded.rsplit(".", 1)

    base_path = project_module_path(root, module_name)
    if base_path is None:
        return None
    return base_path, class_name


def project_class_methods(
    root: Path,
    path: Path,
    class_name: str,
    cache: dict[tuple[str, str], frozenset[str]],
    visiting: set[tuple[str, str]] | None = None,
) -> frozenset[str]:
    """Collect methods declared by a project class and its resolvable project bases."""
    key = (path.resolve().as_posix(), class_name)
    if key in cache:
        return cache[key]

    if visiting is None:
        visiting = set()
    if key in visiting:
        return frozenset()
    visiting.add(key)

    try:
        lines = source_lines(path)
        tree = ast.parse("\n".join(lines) + "\n", filename=path.as_posix())
    except (OSError, SyntaxError):
        visiting.remove(key)
        cache[key] = frozenset()
        return cache[key]

    class_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ),
        None,
    )
    if class_node is None:
        visiting.remove(key)
        cache[key] = frozenset()
        return cache[key]

    methods = {
        node.name
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for base in class_node.bases:
        target = resolve_project_base(root, path, tree, base)
        if target is None:
            continue
        base_path, base_class = target
        methods.update(
            project_class_methods(
                root,
                base_path,
                base_class,
                cache,
                visiting,
            )
        )

    visiting.remove(key)
    cache[key] = frozenset(methods)
    return cache[key]


def inherited_project_methods(
    root: Path,
    path: Path,
    tree: ast.Module,
    class_node: ast.ClassDef,
    cache: dict[tuple[str, str], frozenset[str]],
) -> frozenset[str]:
    methods: set[str] = set()
    for base in class_node.bases:
        target = resolve_project_base(root, path, tree, base)
        if target is None:
            continue
        base_path, base_class = target
        methods.update(project_class_methods(root, base_path, base_class, cache))
    return frozenset(methods)


def guarded_compatibility_loads(tree: ast.Module) -> set[tuple[str, int]]:
    """Identify ``try/name except NameError/name = replacement`` probes."""
    guarded: set[tuple[str, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        fallback_names: set[str] = set()
        for handler in node.handlers:
            catches_name_error = (
                isinstance(handler.type, ast.Name) and handler.type.id == "NameError"
            ) or (
                isinstance(handler.type, ast.Tuple)
                and any(
                    isinstance(item, ast.Name) and item.id == "NameError"
                    for item in handler.type.elts
                )
            )
            if not catches_name_error:
                continue
            for statement in handler.body:
                if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    fallback_names.update(assigned_names(statement))
        for statement in node.body:
            for child in ast.walk(statement):
                if (
                    isinstance(child, ast.Name)
                    and isinstance(child.ctx, ast.Load)
                    and child.id in fallback_names
                ):
                    guarded.add((child.id, child.lineno))
    return guarded


def is_nested_scope(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            return True
        parent = parents.get(parent)
    return False


def contains_float_width_risk(node: ast.AST) -> bool:
    """Return True when a width expression can trivially evaluate to float.

    wx.ListCtrl.SetColumnWidth expects an integer width on recent wxPython.
    Python 3 true division always produces a float, and an explicit float literal
    can propagate through arithmetic. An outer ``int(...)`` is considered an
    explicit and sufficient conversion. The audit deliberately does not guess the
    runtime type of arbitrary names or other function calls.
    """
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "int"
    ):
        return False
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return True
    if isinstance(node, ast.Constant) and isinstance(node.value, float):
        return True
    return any(contains_float_width_risk(child) for child in ast.iter_child_nodes(node))


def audit_ast(
    root: Path,
    path: Path,
    lines: list[str],
    method_cache: dict[tuple[str, str], frozenset[str]] | None = None,
) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    text = "\n".join(lines) + "\n"
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as exc:
        return [Finding("syntax-unparsed", rel, exc.lineno or 0, exc.msg)]

    if method_cache is None:
        method_cache = {}

    findings: list[Finding] = []
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    binding_lines = module_binding_lines(tree)
    guarded_loads = guarded_compatibility_loads(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            detail = ast.get_source_segment(text, node) or "except:"
            findings.append(Finding("bare-except", rel, node.lineno, detail.strip()))

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in {"eval", "exec", "__import__"}:
                detail = ast.get_source_segment(text, node) or f"{func.id}(...)"
                findings.append(
                    Finding("dynamic-execution", rel, node.lineno, detail.strip())
                )
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "SetColumnWidth"
                and len(node.args) >= 2
                and contains_float_width_risk(node.args[1])
            ):
                detail = ast.get_source_segment(text, node.args[1]) or "width expression"
                findings.append(
                    Finding(
                        "wx-column-width-float-risk",
                        rel,
                        node.lineno,
                        detail.strip(),
                    )
                )

        if not (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id in PYTHON2_REMOVED_BUILTINS
        ):
            continue
        if (node.id, node.lineno) in guarded_loads:
            continue
        binding_line = binding_lines.get(node.id)
        if binding_line is not None and (
            is_nested_scope(node, parents) or binding_line <= node.lineno
        ):
            continue
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
        inherited_methods = inherited_project_methods(
            root, path, tree, class_node, method_cache
        )
        available_methods = methods | set(inherited_methods)
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
                and handler.attr not in available_methods
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
    method_cache: dict[tuple[str, str], frozenset[str]] = {}
    for path in files:
        lines = source_lines(path)
        findings.extend(audit_text(root, path, lines))
        findings.extend(audit_compile_warnings(root, path, lines))
        findings.extend(audit_ast(root, path, lines, method_cache))

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

    unparsed = result["counts"].get("syntax-unparsed", 0)
    missing = result["counts"].get("missing-bound-handler", 0)
    sqlite_bytes = result["counts"].get("sqlite-bytes-path", 0)
    python2_builtins = result["counts"].get("python2-removed-builtin", 0)
    if unparsed:
        return 1
    if args.fail_on_missing_handlers and missing:
        return 1
    if args.fail_on_sqlite_bytes_paths and sqlite_bytes:
        return 1
    if args.fail_on_python2_builtins and python2_builtins:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
