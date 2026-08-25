from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_contract_dialog.py"
OPERATIONS_SMOKE = ROOT / "tools" / "smoke_contract_cee_cdd_operations.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_contract_smoke_targets_real_application_context() -> None:
    source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in core
    assert "import Teamworks_core as CORE" in entrypoint
    assert f"MARKER_LINE = '{marker}'" in source
    assert 'ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"' in source
    assert 'CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"' in source
    assert 'PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_contract_smoke.py"' in source
    assert "import Teamworks_core_secondary_contract_smoke as CORE" in source
    assert "from smoke_runtime import" in source
    assert "run_entrypoint(" in source
    assert "write_diagnostic(" in source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert 'env["PYTHONPATH"] = os.pathsep.join(search_paths)' in runtime_source
    assert 'compile(patched_entrypoint, str(PATCHED), "exec")' in source
    assert 'compile(patched_core_source, str(PATCHED_CORE), "exec")' in source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in source


def test_contract_smoke_exercises_ccns_creation_and_database_readback() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:employee" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:new-contract" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:ccns" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:group" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:salary" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:validation" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:save" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_STAGE:database-readback" in source
    assert 'IDcontrat=0' in source
    assert '_SelectContractTypeCode("CDI")' in source
    assert '_SelectConvention("CCNS")' in source
    assert 'choice_ccns_group, "G1"' in source
    assert "_MonthlySalaryDecimal()" in source
    assert "RefreshTrialProposal(force=True)" in source
    assert "trial_value.GetValue() > 0" in source
    assert "_smoke_dialog.Onbouton_suite(None)" in source
    assert "_smoke_dialog.ValidationPages()" in source
    assert "SELECT IDcontrat, convention_code, ccns_group, gross_monthly_salary" in source
    assert 'ReqDEL("contrats", "IDcontrat", _smoke_created_contract_id)' in source
    assert "TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED" in source
    assert "PATCHED.unlink(missing_ok=True)" in source


@pytest.mark.skipif(sys.platform != "win32", reason="smoke wxPython réservé à la qualification Windows")
def test_contract_cee_and_cdd_operations_run_in_real_windows_application() -> None:
    completed = subprocess.run(
        [sys.executable, str(OPERATIONS_SMOKE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )

    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    assert completed.returncode == 0, output
