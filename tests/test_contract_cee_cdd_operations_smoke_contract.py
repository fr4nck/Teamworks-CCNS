from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_contract_cee_cdd_operations.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"


def test_contract_operations_smoke_targets_real_windows_application() -> None:
    source = SMOKE.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in core
    assert "import Teamworks_core as CORE" in entrypoint
    assert f"MARKER_LINE = '{marker}'" in source
    assert 'PATCHED = TEAMWORKS_DIR / "Teamworks_contract_operations_smoke.py"' in source
    assert 'PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_contract_operations_smoke.py"' in source
    assert "import Teamworks_core_contract_operations_smoke as CORE" in source
    assert "run_entrypoint(" in source
    assert 'env["TEAMWORKS_SMOKE_MODE"]' not in source
    assert 'compile(patched_core_source, str(PATCHED_CORE), "exec")' in source
    assert 'compile(patched_entrypoint, str(PATCHED), "exec")' in source
    assert "PATCHED.unlink(missing_ok=True)" in source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in source


def test_contract_operations_smoke_exercises_cee_and_cdd_lifecycle() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:cee" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:cdd-renewal" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_OP_STAGE:cdd-to-cdi" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_OPERATIONS_READY" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_OPERATIONS_FAILED" in source

    assert '_SelectContractTypeCode("CEE")' in source
    assert 'choice_cee_qualification, "BAFA_HOLDER"' in source
    assert 'SaveRate(' in source
    assert '"cee_days_rolling_12_months"] = 7' in source
    assert '"CONFORME" in _smoke_cee.page3.label_cee_preview.GetLabel()' in source

    assert '"CDD_RENEWAL"' in source
    assert '"CDD_TO_CDI"' in source
    assert 'choice_previous_contract, _smoke_previous_contract_id' in source
    assert '"2026-04-01"' in source
    assert 'assert not _smoke_renewal_page.check_trial.GetValue()' in source
    assert 'assert not _smoke_cdi_page.check_trial.GetValue()' in source
    assert '_smoke_renewal_row[4] == "CDD_RENEWAL"' in source
    assert '_smoke_cdi_row[4] == "CDD_TO_CDI"' in source
    assert '_smoke_cdi_row[9] == "2999-01-01"' in source

    assert 'ReqDEL("contrats", "IDcontrat", _smoke_contract_id)' in source
    assert 'ReqDEL("contrats", "IDcontrat", _smoke_previous_contract_id)' in source
    assert 'ReqDEL("contrats_cee_baremes", "IDbareme", _smoke_rate_id)' in source
