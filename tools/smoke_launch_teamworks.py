#!/usr/bin/env python3
"""Launch Teamworks on Windows and validate its deterministic GUI smoke mode."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT = ROOT / "run_teamworks.py"
STARTUP_WINDOW_SECONDS = 30
READY_MARKER = "TEAMWORKS_SMOKE_MAIN_WINDOW_READY"
TAB_MARKERS = tuple(f"TEAMWORKS_SMOKE_TAB_READY:{index}" for index in range(4))
REPORT_PATH = ROOT / "teamworks-startup-smoke.log"


def visible_windows_for_process(process_id: int) -> list[str]:
    """Return titles of visible top-level windows owned by ``process_id``."""
    titles: list[str] = []
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd: int, _lparam: int) -> bool:
        owner_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_pid))
        if owner_pid.value != process_id or not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        titles.append(buffer.value or "<untitled>")
        return True

    user32.EnumWindows(callback_type(callback), 0)
    return titles


def write_report(
    output: str,
    return_code: int | None,
    status: str,
    window_titles: list[str] | None = None,
) -> None:
    window_titles = window_titles or []
    REPORT_PATH.write_text(
        "\n".join(
            [
                f"status={status}",
                f"return_code={return_code}",
                f"startup_window_seconds={STARTUP_WINDOW_SECONDS}",
                f"ready_marker_present={READY_MARKER in output}",
                *(f"tab_marker_{index}_present={marker in output}" for index, marker in enumerate(TAB_MARKERS)),
                f"window_count={len(window_titles)}",
                *(f"window={title}" for title in window_titles),
                "",
                "--- process output ---",
                output,
            ]
        ),
        encoding="utf-8",
    )


def stop_process(process: subprocess.Popen[str]) -> str:
    process.terminate()
    try:
        output, _ = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate(timeout=5)
    return output


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
            "TEAMWORKS_SMOKE_MODE": "main-window",
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

        deadline = time.monotonic() + STARTUP_WINDOW_SECONDS
        observed_titles: list[str] = []
        while time.monotonic() < deadline:
            current_titles = visible_windows_for_process(process.pid)
            for title in current_titles:
                if title not in observed_titles:
                    observed_titles.append(title)

            return_code = process.poll()
            if return_code is not None:
                output, _ = process.communicate(timeout=5)
                ready = READY_MARKER in output
                tabs_ready = all(marker in output for marker in TAB_MARKERS)
                success = return_code == 0 and ready and tabs_ready and bool(observed_titles)
                status = "main-tabs-ready" if success else "invalid-clean-exit"
                write_report(output, return_code, status, observed_titles)
                print(output)
                if success:
                    print(
                        "Teamworks constructed its main window, activated all four "
                        "main tabs, entered the wx event loop, and exited cleanly"
                    )
                    return 0

                print(
                    "Teamworks smoke mode did not satisfy all functional checks: "
                    f"return_code={return_code}, ready={ready}, "
                    f"tabs_ready={tabs_ready}, windows={observed_titles}"
                )
                return 1

            time.sleep(0.25)

        output = stop_process(process)
        write_report(output, process.returncode, "timeout", observed_titles)
        print(output)
        print(
            f"Teamworks did not finish its deterministic smoke mode within "
            f"{STARTUP_WINDOW_SECONDS} seconds"
        )
        return 1
    finally:
        if created_nolog:
            nolog.unlink(missing_ok=True)
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
