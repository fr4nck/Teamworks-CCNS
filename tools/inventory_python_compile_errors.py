#!/usr/bin/env python3
"""Inventory Python files that do not compile under the running interpreter."""

from __future__ import annotations

import argparse
import json
import py_compile
from collections import Counter
from pathlib import Path


def inventory(root: Path) -> dict:
    findings: list[dict] = []
    by_error: Counter[str] = Counter()
    files = sorted(
        path
        for path in root.rglob("*.py")
        if not any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts)
    )

    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            original = exc.exc_value
            error_type = type(original).__name__
            by_error[error_type] += 1
            findings.append(
                {
                    "path": str(path),
                    "error": error_type,
                    "line": getattr(original, "lineno", None),
                    "offset": getattr(original, "offset", None),
                    "message": getattr(original, "msg", str(original)),
                }
            )

    return {
        "root": str(root),
        "python_files": len(files),
        "failed_files": len(findings),
        "successful_files": len(files) - len(findings),
        "by_error": [
            {"error": name, "files": count}
            for name, count in sorted(by_error.items(), key=lambda item: (-item[1], item[0]))
        ],
        "findings": findings,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Audit de compilation Python",
        "",
        f"- Fichiers Python : **{report['python_files']}**",
        f"- Compilation réussie : **{report['successful_files']}**",
        f"- Échecs : **{report['failed_files']}**",
        "",
        "| Erreur | Fichiers |",
        "|---|---:|",
    ]
    for item in report["by_error"]:
        lines.append(f"| `{item['error']}` | {item['files']} |")
    lines.extend(["", "## Détail", ""])
    for item in report["findings"]:
        location = item["path"]
        if item["line"] is not None:
            location += f":{item['line']}"
        lines.append(f"- `{location}` — `{item['error']}` — {item['message']}")
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

    print(
        json.dumps(
            {
                key: report[key]
                for key in ("python_files", "successful_files", "failed_files", "by_error")
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if report["failed_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
