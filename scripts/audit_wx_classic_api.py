#!/usr/bin/env python3
"""Inventorie les appels wxPython Classic encore présents dans les sources actives."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Iterable

CLASSIC_CALLS = {
    "BitmapFromImage",
    "EmptyBitmap",
    "EmptyImage",
    "ImageFromBitmap",
    "NamedColour",
    "NewId",
    "PySimpleApp",
    "StockCursor",
}


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part.startswith(".bak") for part in path.parts):
            continue
        yield path


def decode_source(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8", "iso-8859-15", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="ignore")


def audit(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in iter_python_files(root):
        source = decode_source(path)
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "wx"
                and func.attr in CLASSIC_CALLS
            ):
                continue
            findings.append(
                {
                    "path": str(path),
                    "line": node.lineno,
                    "api": f"wx.{func.attr}",
                }
            )
    return findings


def main() -> int:
    findings = audit(Path("teamworks"))
    print(json.dumps({"count": len(findings), "findings": findings}, indent=2, ensure_ascii=False))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
