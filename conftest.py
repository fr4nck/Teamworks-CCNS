"""Instrumentation temporaire Windows du lifecycle non modal de la fiche."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent
PRELUDE_SMOKE = ROOT / "tools" / "smoke_person_prelude_lifecycle.py"
EVENTLOOP_SMOKE = ROOT / "tools" / "smoke_person_destroy_eventloop.py"


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
def _diagnostic_destroy_eventloop_windows() -> None:
    if sys.platform != "win32":
        return

    failures: list[str] = []

    # Cas conforme au lifecycle wx : 20 fermetures, chacune attend son
    # EVT_WINDOW_DESTROY dans une vraie GUIEventLoop avant la réouverture.
    failure = _run_smoke(EVENTLOOP_SMOKE)
    if failure:
        failures.append(failure)

    # Reproducer historique exécuté dans OnInit, conservé comme contrôle positif.
    failure = _run_smoke(PRELUDE_SMOKE, "close-backup", 1)
    if failure:
        failures.append(failure)

    assert not failures, "\n\n".join(failures)
