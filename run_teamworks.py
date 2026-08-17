#!/usr/bin/env python3
"""Lance Teamworks avec les chemins du dépôt correctement initialisés."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parent
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT = TEAMWORKS_DIR / "Teamworks.py"


def _same_path(left: str, right: Path) -> bool:
    try:
        return Path(left).resolve() == right.resolve()
    except (OSError, RuntimeError):
        return False


def configure_import_paths() -> None:
    """Expose à la fois l'architecture moderne et les modules historiques."""
    for path in (ROOT, TEAMWORKS_DIR):
        sys.path[:] = [value for value in sys.path if not _same_path(value, path)]

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(TEAMWORKS_DIR))


def main() -> int:
    configure_import_paths()
    runpy.run_path(str(ENTRYPOINT), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
