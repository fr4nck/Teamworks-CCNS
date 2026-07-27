from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_presence_dialog.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"


def test_presence_smoke_targets_real_main_window_contract() -> None:
    smoke_source = SMOKE.read_text(encoding="utf-8")
    entrypoint_source = ENTRYPOINT.read_text(encoding="iso-8859-15")

    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
    assert marker in entrypoint_source
    assert f"MARKER_LINE = '{marker}'" in smoke_source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in smoke_source
    assert 'search_paths = [str(ROOT), str(TEAMWORKS_DIR)]' in smoke_source
    assert 'env["PYTHONPATH"] = os.pathsep.join(search_paths)' in smoke_source
    assert 'compile(patched_source, str(PATCHED), "exec")' in smoke_source
    assert "TEAMWORKS_SMOKE_PRESENCE_DIALOG_READY" in smoke_source


def test_presence_smoke_always_writes_a_diagnostic() -> None:
    smoke_source = SMOKE.read_text(encoding="utf-8")

    assert "REPORT_DIR.mkdir(parents=True, exist_ok=True)" in smoke_source
    assert "except Exception:" in smoke_source
    assert "write_diagnostic(return_code=3" in smoke_source
    assert "PATCHED.unlink(missing_ok=True)" in smoke_source
