from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_recruitment_interview.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_interview_smoke_targets_the_real_main_window() -> None:
    source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in core
    assert "import Teamworks_core as CORE" in entrypoint
    assert f"MARKER_LINE = '{marker}'" in source
    assert "DLG_Saisie_entretien" in source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert "import Teamworks_core_secondary_recruitment_interview_smoke as CORE" in source
    assert "TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_READY" in source
    assert "TEAMWORKS_SMOKE_RECRUITMENT_INTERVIEW_FAILED" in source


def test_interview_smoke_qualifies_create_edit_list_and_cleanup() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "create-dialog" in source
    assert "create-save" in source
    assert "create-readback" in source
    assert "edit-dialog" in source
    assert "edit-save" in source
    assert "edit-readback" in source
    assert "list-readback" in source
    assert ".Sauvegarde()" in source
    assert 'getattr(track, "IDentretien", None)' in source
    assert 'ReqDEL("entretiens"' in source
    assert "__TEAMWORKS_SMOKE_ENTRETIEN_CREATE__" in source
    assert "__TEAMWORKS_SMOKE_ENTRETIEN_EDIT__" in source
    assert "PATCHED.unlink(missing_ok=True)" in source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in source