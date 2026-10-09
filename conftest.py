"""Instrumentation temporaire Windows du lifecycle non modal de la fiche."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent
PRELUDE_SMOKE = ROOT / "tools" / "smoke_person_prelude_lifecycle.py"
MAINLOOP_SMOKE = ROOT / "tools" / "smoke_person_mainloop_lifecycle.py"


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

    # Même fiche, même Fermer(), vingt cycles, mais après OnInit dans le vrai
    # MainLoop. Chaque réouverture attend EVT_WINDOW_DESTROY du cycle précédent.
    failure = _run_smoke(MAINLOOP_SMOKE)
    if failure:
        failures.append(failure)

    # Contrôle positif : ancien reproducer synchrone exécuté dans OnInit.
    failure = _run_smoke(PRELUDE_SMOKE, "close-backup", 1)
    if failure:
        failures.append(failure)

    assert not failures, "\n\n".join(failures)
