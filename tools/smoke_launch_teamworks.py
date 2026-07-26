#!/usr/bin/env python3
"""Launch Teamworks on Windows and verify that it creates a real top-level window."""

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
STARTUP_WINDOW_SECONDS = 20
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
        window_titles: list[str] = []
        while time.monotonic() < deadline:
            return_code = process.poll()
            if return_code is not None:
                output, _ = process.communicate(timeout=5)
                write_report(output, return_code, "early-exit")
                print(output)
                print(f"Teamworks exited before creating a stable window with code {return_code}")
                return 1

            window_titles = visible_windows_for_process(process.pid)
            if window_titles:
                output = stop_process(process)
                write_report(output, process.returncode, "window-created", window_titles)
                print(output)
                print(f"Teamworks created {len(window_titles)} visible top-level window(s): {window_titles}")
                return 0

            time.sleep(0.5)

        output = stop_process(process)
        write_report(output, process.returncode, "alive-without-window")
        print(output)
        print(
            f"Teamworks remained alive for {STARTUP_WINDOW_SECONDS} seconds "
            "but created no visible top-level window"
        )
        return 1
    finally:
        if created_nolog:
            nolog.unlink(missing_ok=True)
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
