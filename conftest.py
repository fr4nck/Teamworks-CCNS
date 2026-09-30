"""Instrumentation temporaire de la RC3 pour isoler le crash wx.SearchCtrl.

Sous Linux ce fichier est inerte. Sous Windows, le job de contrats exécute des
reproductions ciblées en processus séparés avant les tests habituels.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parent
SEARCHCTRL_SMOKE = ROOT / "tools" / "smoke_searchctrl_lifecycle.py"
PRELUDE_SMOKE = ROOT / "tools" / "smoke_person_prelude_lifecycle.py"
ORDER_SMOKE = ROOT / "tools" / "smoke_person_close_order.py"


def _run_smoke(script: Path, scenario: str, cycles: int | None = None) -> str | None:
    command = [sys.executable, str(script), "--scenario", scenario]
    if cycles is not None:
        command.extend(["--cycles", str(cycles)])
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=1200,
        check=False,
    )
    output = "\n".join(
        part for part in (completed.stdout, completed.stderr) if part
    )
    print(output)
    if completed.returncode != 0:
        return f"{scenario}: return_code={completed.returncode}\n{output}"
    return None


@pytest.fixture(scope="session", autouse=True)
def _diagnostic_searchctrl_windows() -> None:
    if sys.platform != "win32":
        return

    failures: list[str] = []

    # Contrôle négatif : le SearchCtrl et la sauvegarde seuls restent stables.
    failure = _run_smoke(SEARCHCTRL_SMOKE, "backup-search", 10)
    if failure:
        failures.append(failure)

    # Mesure du seuil de la sauvegarde seule, puis stress de l'ordre réel de
    # fermeture. callbacks-first est l'hypothèse de correctif, current-manual
    # reproduit explicitement l'ordre actuellement codé dans Fermer().
    for scenario in (
        "save-only-1",
        "save-only-2",
        "save-only-3",
        "fermer-20",
        "current-manual-20",
        "callbacks-first-20",
    ):
        failure = _run_smoke(ORDER_SMOKE, scenario)
        if failure:
            failures.append(failure)

    # Garde de comparaison avec le reproducer historique.
    failure = _run_smoke(PRELUDE_SMOKE, "close-backup", 1)
    if failure:
        failures.append(failure)

    assert not failures, "\n\n".join(failures)
