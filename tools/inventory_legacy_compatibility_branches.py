#!/usr/bin/env python3
"""Inventory legacy Python 2 and wxPython Classic compatibility branches."""

from __future__ import annotations

import argparse
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import tokenize


PATTERNS = {
    "six.PY2": re.compile(r"\bsix\.PY2\b"),
    "sys.version_info[0] == 2": re.compile(r"sys\.version_info\s*\[\s*0\s*\]\s*==\s*2"),
    "sys.version_info < (3": re.compile(r"sys\.version_info\s*<\s*\(\s*3"),
    "phoenix PlatformInfo branch": re.compile(r"['\"]phoenix['\"]\s+in\s+wx\.PlatformInfo"),
    "classic PlatformInfo branch": re.compile(r"['\"]phoenix['\"]\s+not\s+in\s+wx\.PlatformInfo"),
}


def read_source(path: Path) -> str:
    data = path.read_bytes()
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        return data.decode(encoding)
    except (SyntaxError, UnicodeDecodeError):
        return data.decode("utf-8", errors="replace")


def inventory(root: Path) -> dict:
    findings = []
    totals = Counter()
    files_by_kind = defaultdict(set)

    for path in sorted(root.rglob("*.py")):
        source = read_source(path)
        for line_number, line in enumerate(source.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            for kind, pattern in PATTERNS.items():
                count = len(pattern.findall(line))
                if not count:
                    continue
                totals[kind] += count
                files_by_kind[kind].add(str(path))
                findings.append(
                    {
                        "kind": kind,
                        "path": str(path),
                        "line": line_number,
                        "count": count,
                        "source": line.strip(),
                    }
                )

    return {
        "root": str(root),
        "total_occurrences": sum(totals.values()),
        "total_files": len({item["path"] for item in findings}),
        "by_kind": [
            {
                "kind": kind,
                "occurrences": totals[kind],
                "files": len(files_by_kind[kind]),
            }
            for kind in sorted(totals, key=lambda name: (-totals[name], name))
        ],
        "findings": findings,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Inventaire des branches de compatibilité legacy",
        "",
        f"- Occurrences détectées : **{report['total_occurrences']}**",
        f"- Fichiers concernés : **{report['total_files']}**",
        "",
        "| Type | Occurrences | Fichiers |",
        "|---|---:|---:|",
    ]
    for item in report["by_kind"]:
        lines.append(
            f"| `{item['kind']}` | {item['occurrences']} | {item['files']} |"
        )
    lines.extend(["", "## Détail", ""])
    for item in report["findings"]:
        lines.append(
            f"- `{item['kind']}` — `{item['path']}:{item['line']}` — `{item['source']}`"
        )
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
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_path:
        Path(args.markdown_path).write_text(
            markdown_report(report), encoding="utf-8"
        )

    print(
        json.dumps(
            {
                key: report[key]
                for key in ("total_occurrences", "total_files", "by_kind")
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
