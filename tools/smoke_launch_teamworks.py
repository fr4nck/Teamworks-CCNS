#!/usr/bin/env python3
"""Launch Teamworks briefly on Windows and fail on an early process exit."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT = ROOT / "run_teamworks.py"
STARTUP_WINDOW_SECONDS = 15
REPORT_PATH = ROOT / "teamworks-startup-smoke.log"


def write_report(output: str, return_code: int | None, status: str) -> None:
    REPORT_PATH.write_text(
        "\n".join(
            [
                f"status={status}",
                f"return_code={return_code}",
                f"startup_window_seconds={STARTUP_WINDOW_SECONDS}",
                "",
                "--- process output ---",
                output,
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    if sys.platform != "win32":
        print("Windows-only smoke test skipped")
        return 0

    REPORT_PATH.unlink(missing_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix="teamworks-smoke-"))
    nolog = TEAMWORKS_DIR / "nolog.txt"
    created_nolog = not nolog.exists()

    env = os.environ.copy()
    env.update(
        {
            "APPDATA": str(sandbox / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(sandbox / "AppData" / "Local"),
            "TEMP": str(sandbox / "Temp"),
            "TMP": str(sandbox / "Temp"),
            "PYTHONUNBUFFERED": "1",
        }
    )
    for key in ("APPDATA", "LOCALAPPDATA", "TEMP", "TMP"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)

    if created_nolog:
        nolog.write_text("CI smoke test\n", encoding="utf-8")

    try:
        process = subprocess.Popen(
            [sys.executable, str(ENTRYPOINT)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        try:
            output, _ = process.communicate(timeout=STARTUP_WINDOW_SECONDS)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                output, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                output, _ = process.communicate(timeout=5)

            write_report(output, process.returncode, "alive")
            print(output)
            print(
                f"Teamworks remained alive for {STARTUP_WINDOW_SECONDS} seconds: "
                "controlled startup smoke passed"
            )
            return 0

        write_report(output, process.returncode, "early-exit")
        print(output)
        print(
            "Teamworks exited before the startup observation window "
            f"with code {process.returncode}"
        )
        return 1
    finally:
        if created_nolog:
            nolog.unlink(missing_ok=True)
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
