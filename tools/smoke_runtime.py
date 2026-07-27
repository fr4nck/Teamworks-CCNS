#!/usr/bin/env python3
"""Infrastructure commune aux smokes fonctionnels Teamworks."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable


DEFAULT_ENCODINGS = ("utf-8", "cp1252", "iso-8859-15")


def decode_output(data: bytes, encodings: Iterable[str] = DEFAULT_ENCODINGS) -> str:
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def build_environment(root: Path, teamworks_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["TEAMWORKS_SMOKE_MODE"] = "main-window"
    search_paths = [str(root), str(teamworks_dir)]
    if env.get("PYTHONPATH"):
        search_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(search_paths)
    return env


def github_error_summary(title: str, output: str, max_lines: int = 40) -> None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    summary = " | ".join(lines[-max_lines:])
    summary = summary.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error title={title}::{summary}")


def write_diagnostic(
    report: Path,
    *,
    return_code: int,
    marker_count: int | None,
    ready_marker: str,
    failure_marker: str,
    output: str,
    ready_label: str = "ready_marker",
) -> None:
    diagnostic = (
        f"return_code={return_code}\n"
        f"entrypoint_marker_count={marker_count}\n"
        f"{ready_label}={ready_marker in output}\n"
        f"failure_marker={failure_marker in output}\n"
        "--- output ---\n"
        f"{output}"
    )
    report.write_text(diagnostic, encoding="utf-8")
    print(diagnostic)


def run_entrypoint(
    patched: Path,
    *,
    root: Path,
    teamworks_dir: Path,
    timeout: int,
) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(patched)],
        cwd=teamworks_dir,
        env=build_environment(root, teamworks_dir),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    output = decode_output(result.stdout) + "\n" + decode_output(result.stderr)
    return result.returncode, output
