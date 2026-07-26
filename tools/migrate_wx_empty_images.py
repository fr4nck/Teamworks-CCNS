#!/usr/bin/env python3
"""Migre les anciens constructeurs d'images wxPython Classic vers Phoenix.

Par défaut, le script analyse les fichiers Python sous ``teamworks`` sans les
modifier. L'option ``--write`` applique uniquement les transformations exactes
suivantes dans le code Python, sans toucher aux chaînes ni aux commentaires :

- ``wx.EmptyBitmap(...)`` -> ``wx.Bitmap(...)``
- ``wx.EmptyImage(...)`` -> ``wx.Image(...)``

L'encodage déclaré par chaque fichier Python est conservé lors de l'écriture.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import tokenize


ROOT = Path("teamworks")
REPLACEMENTS = {
    "EmptyBitmap": "Bitmap",
    "EmptyImage": "Image",
}


def _line_offsets(source: str) -> list[int]:
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _absolute_offset(offsets: list[int], position: tuple[int, int]) -> int:
    line, column = position
    return offsets[line - 1] + column


def _read_source(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    return raw.decode(encoding), encoding


def _write_source(path: Path, source: str, encoding: str) -> None:
    path.write_bytes(source.encode(encoding))


def migrate_source(source: str) -> tuple[str, int]:
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    offsets = _line_offsets(source)
    edits: list[tuple[int, int, str]] = []

    for index in range(len(tokens) - 3):
        first, dot, name, opening = tokens[index:index + 4]
        if (
            first.type == tokenize.NAME
            and first.string == "wx"
            and dot.type == tokenize.OP
            and dot.string == "."
            and name.type == tokenize.NAME
            and name.string in REPLACEMENTS
            and opening.type == tokenize.OP
            and opening.string == "("
        ):
            start = _absolute_offset(offsets, name.start)
            end = _absolute_offset(offsets, name.end)
            edits.append((start, end, REPLACEMENTS[name.string]))

    migrated = source
    for start, end, replacement in reversed(edits):
        migrated = migrated[:start] + replacement + migrated[end:]

    return migrated, len(edits)


def iter_python_files(root: Path):
    if root.is_file():
        if root.suffix == ".py":
            yield root
        return

    yield from sorted(root.rglob("*.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--path", type=Path, default=ROOT)
    args = parser.parse_args()

    total = 0
    for path in iter_python_files(args.path):
        source, encoding = _read_source(path)
        migrated, count = migrate_source(source)
        if not count:
            continue

        total += count
        print(f"{path}: {count} remplacement(s)")
        if args.write:
            _write_source(path, migrated, encoding)

    print(f"Total: {total} remplacement(s)")
    if args.check and total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
