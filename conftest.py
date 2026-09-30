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
CLOSE_BISECT_SMOKE = ROOT / "tools" / "smoke_person_close_reopen_bisect.py"


def _run_smoke(script: Path, scenario: str, cycles: int | None = None) -> str | None:
    command = [
        sys.executable,
        str(script),
        "--scenario",
        scenario,
    ]
    if cycles is not None:
        command.extend(["--cycles", str(cycles)])
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=max(300, (cycles or 2) * 150),
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

    # Contrôle : le composant cible et le couple sauvegarde→SearchCtrl restent
    # stables lorsqu'ils sont exécutés sans le préambule Personne.
    for scenario, cycles in (
        ("backup-search", 10),
        ("params20-backup", 3),
    ):
        failure = _run_smoke(SEARCHCTRL_SMOKE, scenario, cycles)
        if failure:
            failures.append(failure)

    # Bisection fonctionnelle de Fermer(save=True). D'abord le seuil 1/2/3,
    # puis les trois effets supplémentaires par rapport à un Destroy direct :
    # sauvegarde, arrêt des callbacks et refresh de la page Personnes.
    for scenario in (
        "fermer-1",
        "fermer-2",
        "fermer-3",
        "save-only-3",
        "callbacks-only-3",
        "refresh-only-3",
        "save-callbacks-3",
        "save-refresh-3",
        "callbacks-refresh-3",
    ):
        failure = _run_smoke(CLOSE_BISECT_SMOKE, scenario)
        if failure:
            failures.append(failure)

    # Contrôles historiques du diagnostic précédent.
    for scenario, cycles in (
        ("pages-backup", 3),
        ("close-backup", 3),
        ("bug-report-backup", 5),
        ("prelude-backup", 3),
        ("prelude-params10-backup", 2),
        ("prelude-params20-backup", 2),
    ):
        failure = _run_smoke(PRELUDE_SMOKE, scenario, cycles)
        if failure:
            failures.append(failure)

    assert not failures, "\n\n".join(failures)
