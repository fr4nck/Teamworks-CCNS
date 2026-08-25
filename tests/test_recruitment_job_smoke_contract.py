from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_recruitment_job.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_job_smoke_targets_real_recruitment_flow() -> None:
    source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in core
    assert "import Teamworks_core as CORE" in entrypoint
    assert f"MARKER_LINE = '{marker}'" in source
    assert "DLG_Saisie_emploi" in source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert "import Teamworks_core_secondary_recruitment_job_smoke as CORE" in source
    assert "TEAMWORKS_SMOKE_RECRUITMENT_JOB_READY" in source
    assert "TEAMWORKS_SMOKE_RECRUITMENT_JOB_FAILED" in source


def test_job_smoke_qualifies_parent_children_edit_list_and_cleanup() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    assert "create-dialog" in source
    assert "create-save" in source
    assert "create-readback" in source
    assert "edit-dialog" in source
    assert "edit-save" in source
    assert "edit-readback" in source
    assert "list-readback" in source
    assert ".Sauvegarde()" in source
    for table in (
        "emplois_dispo",
        "emplois_fonctions",
        "emplois_affectations",
        "emplois_diffuseurs",
    ):
        assert table in source
    assert 'ReqDEL("emplois", "IDemploi"' in source
    assert "__TEAMWORKS_SMOKE_EMPLOI_CREATE__" in source
    assert "__TEAMWORKS_SMOKE_EMPLOI_EDIT__" in source
    assert 'dict_pages_by_index["recrutement"]' in source
    assert 'getattr(track, "IDemploi", None)' in source
    assert "PATCHED.unlink(missing_ok=True)" in source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in source
