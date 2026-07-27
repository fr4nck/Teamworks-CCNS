from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_contract_dialog.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"


def test_contract_smoke_targets_real_application_context() -> None:
    source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint = ENTRYPOINT.read_text(encoding="iso-8859-15")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in entrypoint
    assert f"MARKER_LINE = '{marker}'" in source
    assert "from smoke_runtime import" in source
    assert "run_entrypoint(" in source
    assert "write_diagnostic(" in source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert 'env["PYTHONPATH"] = os.pathsep.join(search_paths)' in runtime_source
    assert 'compile(patched_source, str(PATCHED), "exec")' in source


def test_contract_smoke_exercises_forward_and_backward_navigation() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "for _smoke_target_page in range(2, 7):" in source
    assert "_smoke_dialog.Onbouton_suite(None)" in source
    assert "for _smoke_target_page in range(5, 0, -1):" in source
    assert "_smoke_dialog.Onbouton_retour(None)" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_DIALOG_READY" in source
    assert "TEAMWORKS_SMOKE_CONTRACT_DIALOG_FAILED" in source
    assert "PATCHED.unlink(missing_ok=True)" in source
