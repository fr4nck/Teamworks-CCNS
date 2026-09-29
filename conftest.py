"""Instrumentation temporaire de la RC3 pour isoler le crash wx.SearchCtrl.

Pytest charge ce fichier automatiquement. Sous Linux il est inerte. Sous Windows,
le job de contrats exécute les reproductions minimales dans des processus séparés
avant les tests habituels. À retirer une fois la cause racine établie.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parent
SEARCHCTRL_SMOKE = ROOT / "tools" / "smoke_searchctrl_lifecycle.py"


@pytest.fixture(scope="session", autouse=True)
def _diagnostic_searchctrl_windows() -> None:
    if sys.platform != "win32":
        return

    failures: list[str] = []
    scenarios = (
        ("buttons-search", 20),
        ("backup-search", 15),
        ("backup-email", 15),
        ("params10-backup", 5),
        ("params15-backup", 5),
        ("params20-backup", 5),
    )
    for scenario, cycles in scenarios:
        completed = subprocess.run(
            [
                sys.executable,
                str(SEARCHCTRL_SMOKE),
                "--scenario",
                scenario,
                "--cycles",
                str(cycles),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=max(300, cycles * 60),
            check=False,
        )
        output = "\n".join(
            part for part in (completed.stdout, completed.stderr) if part
        )
        print(output)
        if completed.returncode != 0:
            failures.append(
                f"{scenario}: return_code={completed.returncode}\n{output}"
            )

    assert not failures, "\n\n".join(failures)
