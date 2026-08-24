#!/usr/bin/env python3
"""Infrastructure commune aux smokes fonctionnels Teamworks."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable


DEFAULT_ENCODINGS = ("utf-8",)
TIMEOUT_RETURN_CODE = 124


def console_safe_text(value: str, encoding: str | None = None) -> str:
    """Préserve le diagnostic même si la console Windows n'accepte pas Unicode."""
    target_encoding = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    return value.encode(target_encoding, errors="backslashreplace").decode(
        target_encoding
    )


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
    env["TEAMWORKS_LOG_DIR"] = str(root / "artifacts" / "runtime-crash")
    env["PYTHONUTF8"] = "1"
    search_paths = [str(root), str(teamworks_dir)]
    if env.get("PYTHONPATH"):
        search_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(search_paths)
    return env


def github_error_summary(title: str, output: str, max_lines: int = 40) -> None:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    summary = " | ".join(lines[-max_lines:])
    summary = summary.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(console_safe_text(f"::error title={title}::{summary}"))


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
    print(console_safe_text(diagnostic))


def _append_crash_reports(output: str, log_dir: Path) -> str:
    if not log_dir.exists():
        return output
    reports = sorted(
        path
        for path in log_dir.glob("*.txt")
        if path.name.startswith(("crash-", "native-crash-", "freeze-"))
    )
    for report in reports:
        try:
            content = report.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        output += f"\n--- {report.name} ---\n{content}\n"
    return output


def run_entrypoint(
    patched: Path,
    *,
    root: Path,
    teamworks_dir: Path,
    timeout: int,
) -> tuple[int, str]:
    log_dir = root / "artifacts" / "runtime-crash" / patched.stem
    env = build_environment(root, teamworks_dir)
    env["TEAMWORKS_LOG_DIR"] = str(log_dir)
    try:
        result = subprocess.run(
            [sys.executable, str(patched)],
            cwd=teamworks_dir,
            env=env,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        output = decode_output(stdout) + "\n" + decode_output(stderr)
        output += f"\nTEAMWORKS_SMOKE_TIMEOUT:{timeout}\n"
        output = _append_crash_reports(output, log_dir)
        return TIMEOUT_RETURN_CODE, output

    output = decode_output(result.stdout) + "\n" + decode_output(result.stderr)
    output = _append_crash_reports(output, log_dir)
    return result.returncode, output
