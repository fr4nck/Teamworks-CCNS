#!/usr/bin/env python3
"""Inventory Python source encodings before the UTF-8 normalization lot."""

from __future__ import annotations

import argparse
import json
import tokenize
from collections import Counter
from pathlib import Path


def detect_encoding(path: Path) -> str:
    with path.open("rb") as stream:
        encoding, _ = tokenize.detect_encoding(stream.readline)
    return encoding.lower().replace("_", "-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("teamworks"))
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    entries = []
    counts: Counter[str] = Counter()
    for path in sorted(args.path.rglob("*.py")):
        try:
            encoding = detect_encoding(path)
            error = None
        except (SyntaxError, UnicodeDecodeError) as exc:
            encoding = "undetected"
            error = str(exc)
        counts[encoding] += 1
        entries.append({
            "path": path.as_posix(),
            "encoding": encoding,
            "error": error,
        })

    payload = {
        "root": args.path.as_posix(),
        "total_files": len(entries),
        "counts": dict(sorted(counts.items())),
        "non_utf8_files": [
            entry for entry in entries
            if entry["encoding"] not in {"utf-8", "utf-8-sig"}
        ],
    }

    if args.json:
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    lines = [
        "# Inventaire des encodages Python",
        "",
        f"- Racine : `{payload['root']}`",
        f"- Fichiers Python : **{payload['total_files']}**",
        f"- Fichiers non UTF-8 : **{len(payload['non_utf8_files'])}**",
        "",
        "## Répartition",
        "",
    ]
    for encoding, count in payload["counts"].items():
        lines.append(f"- `{encoding}` : **{count}**")

    lines.extend(["", "## Fichiers non UTF-8", ""])
    if payload["non_utf8_files"]:
        for entry in payload["non_utf8_files"]:
            suffix = f" — {entry['error']}" if entry["error"] else ""
            lines.append(f"- `{entry['path']}` : `{entry['encoding']}`{suffix}")
    else:
        lines.append("Aucun.")

    markdown = "\n".join(lines) + "\n"
    if args.markdown:
        args.markdown.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
