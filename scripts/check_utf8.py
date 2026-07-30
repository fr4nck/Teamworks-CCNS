#!/usr/bin/env python
"""Reject non-UTF-8 tracked text and known mojibake sequences."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OBSOLETE_COOKIE = re.compile(
    rb"coding\s*[:=]\s*(?:iso-8859-\d+|latin-?1|cp1252|windows-1252)",
    re.IGNORECASE,
)

# Code points are assembled here so this audit does not contain the forbidden
# sequences as literal source text.
FORBIDDEN_SEQUENCES = tuple(
    bytes.fromhex(value).decode("utf-8")
    for value in (
        "efbfbd",
        "c383c2a9",
        "c383c2a8",
        "c383c2aa",
        "c383c2ab",
        "c383c2a0",
        "c383c2a2",
        "c383c2ae",
        "c383c2af",
        "c383c2b4",
        "c383c2b9",
        "c383c2bb",
        "c383c2bc",
        "c383c2a7",
        "c3a2e282ace284a2",
        "c3a2e282ace2809c",
        "c3a2e282ace2809d",
        "c382c2a0",
        "c382c2b0",
        "c385e2809c",
        "c3afe280bdc2bd",
    )
)


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
    )
    return [
        ROOT / name
        for name in output.decode("utf-8").split("\0")
        if name
    ]


def audit_file(path: Path) -> list[str]:
    raw = path.read_bytes()
    if b"\0" in raw:
        return []

    relative = path.relative_to(ROOT).as_posix()
    errors = []
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return [f"{relative}: fichier texte non UTF-8 ({exc})"]

    if OBSOLETE_COOKIE.search(raw[:300]):
        errors.append(f"{relative}: déclaration d'encodage source obsolète")

    for sequence in FORBIDDEN_SEQUENCES:
        if sequence in text:
            errors.append(
                f"{relative}: séquence mojibake interdite "
                f"(U+{ord(sequence[0]):04X})"
            )
            break
    return errors


def main() -> int:
    errors = [
        error
        for path in tracked_files()
        for error in audit_file(path)
    ]
    if errors:
        print("Échec de la politique UTF-8 :", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Politique UTF-8 validée pour tous les fichiers texte suivis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
