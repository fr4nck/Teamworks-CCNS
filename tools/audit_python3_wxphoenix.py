#!/usr/bin/env python3
"""Inventorie les reliquats Python 2 et wxPython Classic du dépôt."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import re
import sys


PATTERNS = {
    "raw_input": re.compile(r"\braw_input\s*\("),
    "unicode": re.compile(r"\bunicode\s*\("),
    "xrange": re.compile(r"\bxrange\s*\("),
    "has_key": re.compile(r"\.has_key\s*\("),
    "iteritems": re.compile(r"\.iteritems\s*\("),
    "six.MAXSIZE": re.compile(r"\bsix\.MAXSIZE\b"),
    "wx.PySimpleApp": re.compile(r"\bwx\.PySimpleApp\b"),
    "wx.EmptyBitmap": re.compile(r"\bwx\.EmptyBitmap\b"),
    "wx.EmptyImage": re.compile(r"\bwx\.EmptyImage\b"),
    "InsertStringItem": re.compile(r"\.InsertStringItem\s*\("),
}


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        yield path


def audit(root: Path):
    counts = Counter()
    offenders = defaultdict(list)

    for path in iter_python_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    counts[name] += 1
                    offenders[name].append(f"{path}:{line_number}")

    return counts, offenders


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="teamworks")
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        parser.error(f"répertoire introuvable : {root}")

    counts, offenders = audit(root)

    print("Audit Python 3 / wxPython Phoenix")
    print(f"Racine : {root}")
    print()

    for name in PATTERNS:
        print(f"{name:18} {counts[name]:4}")
        if args.details:
            for location in offenders[name]:
                print(f"  - {location}")

    return 1 if any(counts.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
