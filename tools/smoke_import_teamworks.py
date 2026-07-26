#!/usr/bin/env python3
"""Smoke test du socle et de l'import du point d'entrée Teamworks."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
import sys


CORE_MODULES = (
    "wx",
    "six",
    "PIL",
    "reportlab",
    "dateutil",
    "numpy",
    "matplotlib",
    "xlsxwriter",
    "appdirs",
    "chardet",
    "Crypto",
    "feedparser",
    "icalendar",
    "mailjet_rest",
    "mysql.connector",
)


def main() -> int:
    failures: list[str] = []
    for module_name in CORE_MODULES:
        try:
            importlib.import_module(module_name)
            print(f"OK dependency: {module_name}")
        except Exception as exc:  # pragma: no cover - diagnostic CI
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")

    repository_root = Path(__file__).resolve().parents[1]
    teamworks_root = repository_root / "teamworks"
    os.chdir(teamworks_root)
    sys.path.insert(0, str(teamworks_root))
    sys.path.insert(0, str(repository_root))

    try:
        importlib.import_module("Teamworks")
        print("OK entrypoint import: Teamworks")
    except Exception as exc:  # pragma: no cover - diagnostic CI
        failures.append(f"Teamworks: {type(exc).__name__}: {exc}")

    if failures:
        print("\nSmoke test failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nTeamworks Python 3.11 runtime smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
