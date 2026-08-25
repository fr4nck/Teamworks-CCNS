#!/usr/bin/env python3
"""Exécute les parcours critiques du module Recrutement."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SMOKES = (
    ("candidature", ROOT / "tools" / "smoke_recruitment_candidate.py"),
    ("entretien", ROOT / "tools" / "smoke_recruitment_interview.py"),
)
READY_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_RECRUITMENT_FAILED"


def main() -> int:
    failures: list[tuple[str, int]] = []
    for label, script in SMOKES:
        print(f"TEAMWORKS_SMOKE_RECRUITMENT_STAGE:{label}", flush=True)
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            check=False,
        )
        if completed.returncode != 0:
            failures.append((label, completed.returncode))

    if failures:
        for label, return_code in failures:
            print(
                f"TEAMWORKS_SMOKE_RECRUITMENT_CHILD_FAILED:{label}:{return_code}",
                flush=True,
            )
        print(FAILURE_MARKER, flush=True)
        return 1

    print(READY_MARKER, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
