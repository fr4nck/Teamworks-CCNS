from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_pmsl_contracts_21h.py"


def test_pmsl_contracts_21h_smoke_covers_real_priority_cases() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "TEAMWORKS_SMOKE_PMSL_21H_STAGE:cdd-1" in source
    assert "TEAMWORKS_SMOKE_PMSL_21H_STAGE:cdd-2" in source
    assert "TEAMWORKS_SMOKE_PMSL_21H_STAGE:cdd-to-cdi" in source
    assert 'page.weekly_hours.SetValue(21.0)' in source
    assert 'page.SelectChoice(page.choice_ccns_group, "G1")' in source
    assert 'page._SelectContractTypeCode("CDD")' in source
    assert '"CDD_TO_CDI"' in source
    assert '"2999-01-01"' in source
    assert "TEAMWORKS_SMOKE_PMSL_CONTRACTS_21H_READY" in source


@pytest.mark.skipif(sys.platform != "win32", reason="UAT wxPython réservée à la qualification Windows")
def test_pmsl_contracts_21h_run_in_real_windows_application() -> None:
    completed = subprocess.run(
        [sys.executable, str(SMOKE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    assert completed.returncode == 0, output
