#!/usr/bin/env python3
"""Inventory imports that are neither stdlib nor local Teamworks modules."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path


def local_roots(root: Path) -> set[str]:
    roots = {root.name}
    for child in root.iterdir():
        if child.is_dir() or child.suffix == ".py":
            roots.add(child.stem)
    return roots


def imported_root(node: ast.AST) -> list[tuple[str, int]]:
    if isinstance(node, ast.Import):
        return [(alias.name.split(".")[0], node.lineno) for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [(node.module.split(".")[0], node.lineno)]
    return []


def inventory(root: Path) -> dict:
    local = local_roots(root)
    stdlib = set(sys.stdlib_module_names)
    findings: list[dict] = []
    files_by_module: dict[str, set[str]] = defaultdict(set)

    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(
            path.read_text(encoding="utf-8", errors="replace"),
            filename=str(path),
        )
        for node in ast.walk(tree):
            for module, line in imported_root(node):
                if module in stdlib or module in local or module == "__future__":
                    continue
                files_by_module[module].add(str(path))
                findings.append({"module": module, "path": str(path), "line": line})

    modules = [
        {"module": module, "files": len(paths), "paths": sorted(paths)}
        for module, paths in sorted(files_by_module.items(), key=lambda item: (-len(item[1]), item[0].lower()))
    ]
    return {
        "root": str(root),
        "external_modules": len(modules),
        "affected_files": len({item["path"] for item in findings}),
        "modules": modules,
        "findings": sorted(findings, key=lambda item: (item["module"].lower(), item["path"], item["line"])),
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Inventaire des imports externes",
        "",
        f"- Modules externes : **{report['external_modules']}**",
        f"- Fichiers concernés : **{report['affected_files']}**",
        "",
        "| Module | Fichiers |",
        "|---|---:|",
    ]
    for item in report["modules"]:
        lines.append(f"| `{item['module']}` | {item['files']} |")
    lines.extend(["", "## Détail", ""])
    for item in report["findings"]:
        lines.append(f"- `{item['module']}` — `{item['path']}:{item['line']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="teamworks")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--markdown", dest="markdown_path")
    args = parser.parse_args()

    report = inventory(Path(args.path))
    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.markdown_path:
        Path(args.markdown_path).write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("external_modules", "affected_files", "modules")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
