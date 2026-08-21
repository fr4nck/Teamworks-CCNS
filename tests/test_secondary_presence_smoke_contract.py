from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_presence_dialog.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_presence_smoke_targets_real_main_window_contract() -> None:
    smoke_source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint_source = ENTRYPOINT.read_text(encoding="utf-8")
    core_source = CORE.read_text(encoding="utf-8")

    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
    assert marker in core_source
    assert "import Teamworks_core as CORE" in entrypoint_source
    assert f"MARKER_LINE = '{marker}'" in smoke_source
    assert 'ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"' in smoke_source
    assert 'CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"' in smoke_source
    assert 'PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_presence_smoke.py"' in smoke_source
    assert "import Teamworks_core_secondary_presence_smoke as CORE" in smoke_source
    assert "from smoke_runtime import" in smoke_source
    assert "run_entrypoint(" in smoke_source
    assert "write_diagnostic(" in smoke_source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert 'search_paths = [str(root), str(teamworks_dir)]' in runtime_source
    assert 'env["PYTHONPATH"] = os.pathsep.join(search_paths)' in runtime_source
    assert 'compile(patched_entrypoint, str(PATCHED), "exec")' in smoke_source
    assert 'compile(patched_core_source, str(PATCHED_CORE), "exec")' in smoke_source
    assert "TEAMWORKS_SMOKE_PRESENCE_DIALOG_READY" in smoke_source


def test_presence_smoke_always_writes_a_diagnostic() -> None:
    smoke_source = SMOKE.read_text(encoding="utf-8")

    assert "REPORT_DIR.mkdir(parents=True, exist_ok=True)" in smoke_source
    assert "except Exception:" in smoke_source
    assert "return_code=3" in smoke_source
    assert "write_diagnostic(" in smoke_source
    assert "PATCHED.unlink(missing_ok=True)" in smoke_source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in smoke_source