"""Instrumentation temporaire Windows du lifecycle non modal de la fiche."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent
PRELUDE_SMOKE = ROOT / "tools" / "smoke_person_prelude_lifecycle.py"
MAINLOOP_SMOKE = ROOT / "tools" / "smoke_person_mainloop_lifecycle.py"
CLOSE_MATRIX_SMOKE = ROOT / "tools" / "smoke_person_mainloop_close_matrix.py"
CLOSE_MATRIX_SCENARIOS = (
    "destroy",
    "save-destroy",
    "callbacks-destroy",
    "refresh-destroy",
    "save-callbacks-destroy",
    "callbacks-save-destroy",
    "fermer-nosave",
    "fermer-save",
)


def _run_smoke(script: Path, scenario: str | None = None, cycles: int | None = None) -> str | None:
    command = [sys.executable, str(script)]
    if scenario is not None:
        command.extend(["--scenario", scenario])
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
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    print(output)
    if completed.returncode != 0:
        label = scenario or script.name
        return f"{label}: return_code={completed.returncode}\n{output}"
    return None


@pytest.fixture(scope="session", autouse=True)
def _diagnostic_mainloop_windows() -> None:
    if sys.platform != "win32":
        return

    failures: list[str] = []

    # Bisection native : chaque scénario vit dans son propre processus afin
    # qu'une corruption du tas n'empêche pas les scénarios suivants de parler.
    for scenario in CLOSE_MATRIX_SCENARIOS:
        failure = _run_smoke(CLOSE_MATRIX_SMOKE, scenario)
        if failure:
            failures.append(failure)

    # Contrôle de référence : le reproducer synchrone historique reste vert.
    failure = _run_smoke(PRELUDE_SMOKE, "close-backup", 1)
    if failure:
        failures.append(failure)

    assert not failures, "\n\n".join(failures)
