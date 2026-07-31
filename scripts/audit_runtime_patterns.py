#!/usr/bin/env python3
"""Inventorie les motifs de fragilité runtime de Teamworks sans modifier le code."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

PATTERNS = {
    "resultat_req_index_0": re.compile(r"ResultatReq\(\)\s*\[\s*0\s*\]"),
    "selection_index_0": re.compile(r"(?:Selection|GetSelections?|GetSelectedObjects?)\([^\n]*\)\s*\[\s*0\s*\]"),
    "call_index_0": re.compile(r"\b[A-Za-z_]\w*\([^\n]*\)\s*\[\s*0\s*\]"),
    "bare_except": re.compile(r"^\s*except\s*:\s*(?:#.*)?$", re.MULTILINE),
    "except_pass": re.compile(r"except(?:\s+Exception)?\s*:\s*(?:\n\s+)?pass\b", re.MULTILINE),
    "set_column_width": re.compile(r"SetColumnWidth\([^\n]+\)"),
    "recherche_pays": re.compile(r"Recherche_Pays\("),
}


def read_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--json", dest="json_path")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    findings: list[dict[str, object]] = []

    for path in sorted(root.rglob("*.py")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        source = read_source(path)
        lines = source.splitlines()
        for category, pattern in PATTERNS.items():
            for match in pattern.finditer(source):
                line = source.count("\n", 0, match.start()) + 1
                findings.append({
                    "category": category,
                    "file": path.relative_to(root).as_posix(),
                    "line": line,
                    "text": lines[line - 1].strip()[:240],
                })

    counts = Counter(item["category"] for item in findings)
    payload = {"counts": dict(counts), "findings": findings}
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for category in PATTERNS:
        print(f"{category}: {counts.get(category, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
