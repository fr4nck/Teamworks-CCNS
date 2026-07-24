#!/usr/bin/env python3
"""Inventory common Python 2 runtime constructs still present in Teamworks."""

from __future__ import annotations

import argparse
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import tokenize


PATTERNS = {
    "xrange": re.compile(r"\bxrange\s*\("),
    "dict.iteritems": re.compile(r"\.iteritems\s*\("),
    "dict.iterkeys": re.compile(r"\.iterkeys\s*\("),
    "dict.itervalues": re.compile(r"\.itervalues\s*\("),
    "dict.has_key": re.compile(r"\.has_key\s*\("),
    "basestring": re.compile(r"\bbasestring\b"),
    "unicode": re.compile(r"\bunicode\b"),
    "long": re.compile(r"\blong\b"),
    "raw_input": re.compile(r"\braw_input\s*\("),
    "file_builtin": re.compile(r"(?<![\w.])file\s*\("),
    "execfile": re.compile(r"\bexecfile\s*\("),
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
    files_by_risk = defaultdict(set)

    for path in sorted(root.rglob("*.py")):
        source = read_source(path)
        for line_number, line in enumerate(source.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            for risk, pattern in PATTERNS.items():
                count = len(pattern.findall(line))
                if not count:
                    continue
                totals[risk] += count
                files_by_risk[risk].add(str(path))
                findings.append(
                    {
                        "risk": risk,
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
        "by_risk": [
            {
                "risk": risk,
                "occurrences": totals[risk],
                "files": len(files_by_risk[risk]),
            }
            for risk in sorted(totals, key=lambda name: (-totals[name], name))
        ],
        "findings": findings,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Inventaire des risques Python 3 restants",
        "",
        f"- Occurrences détectées : **{report['total_occurrences']}**",
        f"- Fichiers concernés : **{report['total_files']}**",
        "",
        "| Risque | Occurrences | Fichiers |",
        "|---|---:|---:|",
    ]
    for item in report["by_risk"]:
        lines.append(
            f"| `{item['risk']}` | {item['occurrences']} | {item['files']} |"
        )
    lines.extend(["", "## Détail", ""])
    for item in report["findings"]:
        lines.append(
            f"- `{item['risk']}` — `{item['path']}:{item['line']}` — `{item['source']}`"
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
                for key in ("total_occurrences", "total_files", "by_risk")
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
