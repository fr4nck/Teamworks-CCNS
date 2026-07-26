#!/usr/bin/env python3
"""Lance Teamworks avec les chemins du dépôt correctement initialisés."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parent
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT = TEAMWORKS_DIR / "Teamworks.py"


def configure_import_paths() -> None:
    """Expose à la fois l'architecture moderne et les modules historiques."""
    for path in (ROOT, TEAMWORKS_DIR):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def main() -> int:
    configure_import_paths()
    runpy.run_path(str(ENTRYPOINT), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
