"""Instrumentation temporaire Windows du lifecycle non modal de la fiche."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent
PRELUDE_SMOKE = ROOT / "tools" / "smoke_person_prelude_lifecycle.py"
DESTROY_SMOKE = ROOT / "tools" / "smoke_person_destroy_completion.py"


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
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    print(output)
    if completed.returncode != 0:
        return f"{scenario}: return_code={completed.returncode}\n{output}"
    return None


@pytest.fixture(scope="session", autouse=True)
def _diagnostic_destroy_completion_windows() -> None:
    if sys.platform != "win32":
        return

    failures: list[str] = []
    for scenario in ("yield-20", "await-destroy-20"):
        failure = _run_smoke(DESTROY_SMOKE, scenario)
        if failure:
            failures.append(failure)

    # Reproducer historique, conservé pour corréler le diagnostic au défaut.
    failure = _run_smoke(PRELUDE_SMOKE, "close-backup", 1)
    if failure:
        failures.append(failure)

    assert not failures, "\n\n".join(failures)
