#!/usr/bin/env python3
"""Inventory remaining wxPython Classic API usages in Teamworks source files.

The inventory deliberately excludes API names that are still valid in Phoenix,
such as ``TreeCtrl.AppendItem``. Patterns are restricted to obsolete call forms
so already-migrated replacements such as ``wx.NewIdRef`` are not reported.
"""

from __future__ import annotations

import argparse
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import tokenize


PATTERNS = {
    "AppendMenu": re.compile(r"\.AppendMenu\s*\("),
    "SetToolTipString": re.compile(r"\.SetToolTipString\s*\("),
    "GetClientSizeTuple": re.compile(r"\.GetClientSizeTuple\s*\("),
    "PySimpleApp": re.compile(r"\bwx\.PySimpleApp\s*\("),
    "NewId": re.compile(r"\bwx\.NewId\s*\("),
    "BitmapFromImage": re.compile(r"\bwx\.BitmapFromImage\s*\("),
    "ImageFromStream": re.compile(r"\bwx\.ImageFromStream\s*\("),
    "EmptyBitmap": re.compile(r"\bwx\.EmptyBitmap\s*\("),
    "EmptyImage": re.compile(r"\bwx\.EmptyImage\s*\("),
    "InsertStringItem": re.compile(r"\.InsertStringItem\s*\("),
    "SetStringItem": re.compile(r"\.SetStringItem\s*\("),
    "SetPyData": re.compile(r"\.SetPyData\s*\("),
    "GetPyData": re.compile(r"\.GetPyData\s*\("),
    "wx.PyValidator": re.compile(r"\bwx\.PyValidator\b"),
    "wx.PyControl": re.compile(r"\bwx\.PyControl\b"),
    "wx.PyPanel": re.compile(r"\bwx\.PyPanel\b"),
    "wx.PyWindow": re.compile(r"\bwx\.PyWindow\b"),
    "wx.OPEN": re.compile(r"\bwx\.OPEN\b"),
    "wx.SAVE": re.compile(r"\bwx\.SAVE\b"),
    "wx.OVERWRITE_PROMPT": re.compile(r"\bwx\.OVERWRITE_PROMPT\b"),
    "wx.CHANGE_DIR": re.compile(r"\bwx\.CHANGE_DIR\b"),
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
    files_by_api = defaultdict(set)

    for path in sorted(root.rglob("*.py")):
        source = read_source(path)
        for line_number, line in enumerate(source.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            for api, pattern in PATTERNS.items():
                count = len(pattern.findall(line))
                if not count:
                    continue
                totals[api] += count
                files_by_api[api].add(str(path))
                findings.append(
                    {
                        "api": api,
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
        "by_api": [
            {
                "api": api,
                "occurrences": totals[api],
                "files": len(files_by_api[api]),
            }
            for api in sorted(totals, key=lambda name: (-totals[name], name))
        ],
        "findings": findings,
    }


def markdown_report(report: dict) -> str:
    lines = [
        "# Inventaire wxPython Classic restant",
        "",
        f"- Occurrences détectées : **{report['total_occurrences']}**",
        f"- Fichiers concernés : **{report['total_files']}**",
        "",
        "| API | Occurrences | Fichiers |",
        "|---|---:|---:|",
    ]
    for item in report["by_api"]:
        lines.append(f"| `{item['api']}` | {item['occurrences']} | {item['files']} |")
    lines.extend(["", "## Détail", ""])
    for item in report["findings"]:
        lines.append(
            f"- `{item['api']}` — `{item['path']}:{item['line']}` — `{item['source']}`"
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
        Path(args.markdown_path).write_text(markdown_report(report), encoding="utf-8")

    print(json.dumps({key: report[key] for key in ("total_occurrences", "total_files", "by_api")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
