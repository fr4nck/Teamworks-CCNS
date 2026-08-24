from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_recruitment.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_recruitment_smoke_runs_the_active_shell_with_instrumented_core() -> None:
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
    assert 'PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_secondary_recruitment_smoke.py"' in source
    assert "import Teamworks_core_secondary_recruitment_smoke as CORE" in source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert 'compile(patched_entrypoint, str(PATCHED), "exec")' in source
    assert 'compile(patched_core_source, str(PATCHED_CORE), "exec")' in source
    assert "PATCHED.unlink(missing_ok=True)" in source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in source


def test_recruitment_smoke_exercises_lists_filters_and_actions() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "CTRL_Page_candidatures" in source
    assert "OL_candidatures" in source
    assert "GetListeFiltres" in source
    assert "SortBy(1)" in source
    assert "bouton_candidatures_ajouter.IsEnabled()" in source
    assert "bouton_entretiens_ajouter.IsEnabled()" in source
    assert "TEAMWORKS_SMOKE_RECRUITMENT_READY" in source
    assert "TEAMWORKS_SMOKE_RECRUITMENT_FAILED" in source