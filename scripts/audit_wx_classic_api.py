#!/usr/bin/env python3
"""Inventorie les références wxPython Classic encore présentes dans les sources actives."""

from __future__ import annotations

import ast
import json
import tokenize
from pathlib import Path
from typing import Iterable

CLASSIC_APIS = {
    "BitmapFromImage",
    "EmptyBitmap",
    "EmptyImage",
    "ImageFromBitmap",
    "NamedColour",
    "NewId",
    "PySimpleApp",
    "StockCursor",
}

KNOWN_LEGACY_REFERENCES: set[tuple[str, str]] = set()


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part.startswith(".bak") for part in path.parts):
            continue
        yield path


def decode_source(path: Path) -> str:
    with path.open("rb") as stream:
        encoding, _ = tokenize.detect_encoding(stream.readline)
    return path.read_bytes().decode(encoding)


def audit(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in iter_python_files(root):
        source = decode_source(path)
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            findings.append(
                {
                    "path": str(path),
                    "line": exc.lineno or 0,
                    "api": "parse-error",
                    "detail": exc.msg,
                }
            )
            continue

        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "wx"
                and node.attr in CLASSIC_APIS
            ):
                continue
            findings.append(
                {
                    "path": str(path),
                    "line": node.lineno,
                    "api": f"wx.{node.attr}",
                }
            )
    return findings


def unexpected_findings(findings: list[dict[str, object]]) -> list[dict[str, object]]:
    unexpected: list[dict[str, object]] = []
    for finding in findings:
        key = (str(finding["path"]), str(finding["api"]))
        if key not in KNOWN_LEGACY_REFERENCES:
            unexpected.append(finding)
    return unexpected


def main() -> int:
    findings = audit(Path("teamworks"))
    unexpected = unexpected_findings(findings)
    print(
        json.dumps(
            {
                "count": len(findings),
                "unexpected_count": len(unexpected),
                "findings": findings,
                "unexpected": unexpected,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
