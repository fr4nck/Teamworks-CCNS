#!/usr/bin/env python3
"""Inventory executable Python 2 runtime constructs still present in Teamworks."""

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


IGNORED_TOKEN_TYPES = {tokenize.COMMENT, tokenize.STRING}


def read_source(path: Path) -> str:
    data = path.read_bytes()
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        return data.decode(encoding)
    except (SyntaxError, UnicodeDecodeError):
        return data.decode("utf-8", errors="replace")


def executable_source(source: str) -> str:
    """Blank strings and comments while preserving line and column positions."""
    lines = source.splitlines(keepends=True)
    mutable = [list(line) for line in lines]

    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type not in IGNORED_TOKEN_TYPES:
                continue
            (start_line, start_col) = token.start
            (end_line, end_col) = token.end
            for line_number in range(start_line, end_line + 1):
                line = mutable[line_number - 1]
                first_col = start_col if line_number == start_line else 0
                last_col = end_col if line_number == end_line else len(line)
                for column in range(first_col, min(last_col, len(line))):
                    if line[column] not in "\r\n":
                        line[column] = " "
    except (tokenize.TokenError, IndentationError):
        # The repository still contains historical files that may not tokenize
        # completely. Returning the original source keeps the inventory useful
        # for those files instead of aborting the full report.
        return source

    return "".join("".join(line) for line in mutable)


def inventory(root: Path) -> dict:
    findings = []
    totals = Counter()
    files_by_risk = defaultdict(set)

    for path in sorted(root.rglob("*.py")):
        source = read_source(path)
        executable = executable_source(source)
        original_lines = source.splitlines()
        for line_number, line in enumerate(executable.splitlines(), start=1):
            for risk, pattern in PATTERNS.items():
                count = len(pattern.findall(line))
                if not count:
                    continue
                totals[risk] += count
                files_by_risk[risk].add(str(path))
                original = original_lines[line_number - 1] if line_number <= len(original_lines) else line
                findings.append(
                    {
                        "risk": risk,
                        "path": str(path),
                        "line": line_number,
                        "count": count,
                        "source": original.strip(),
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
