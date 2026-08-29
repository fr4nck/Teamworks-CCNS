from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_runtime_risks.py"


def run_audit(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_runtime_risk_audit_fails_closed_on_unparsed_python(tmp_path: Path) -> None:
    source_root = tmp_path / "teamworks"
    source_root.mkdir()
    (source_root / "broken.py").write_text("def broken(:\n", encoding="utf-8")

    result = run_audit(tmp_path)

    assert result.returncode == 1
    assert "syntax-unparsed: 1" in result.stdout


def test_runtime_risk_audit_stays_successful_for_parseable_python(tmp_path: Path) -> None:
    source_root = tmp_path / "teamworks"
    source_root.mkdir()
    (source_root / "ok.py").write_text("VALUE = 1\n", encoding="utf-8")

    result = run_audit(tmp_path)

    assert result.returncode == 0
    assert "Python files audited: 1" in result.stdout
