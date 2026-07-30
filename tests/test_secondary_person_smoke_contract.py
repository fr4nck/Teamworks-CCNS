from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_secondary_person_dialog.py"
RUNTIME = ROOT / "tools" / "smoke_runtime.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"


def test_person_smoke_targets_the_real_example_ready_marker() -> None:
    smoke_source = SMOKE.read_text(encoding="utf-8")
    runtime_source = RUNTIME.read_text(encoding="utf-8")
    entrypoint_source = ENTRYPOINT.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in entrypoint_source
    assert f"MARKER_LINE = '{marker}'" in smoke_source
    assert "from smoke_runtime import" in smoke_source
    assert "run_entrypoint(" in smoke_source
    assert "write_diagnostic(" in smoke_source
    assert 'env["TEAMWORKS_SMOKE_MODE"] = "main-window"' in runtime_source
    assert 'env["PYTHONPATH"] = os.pathsep.join(search_paths)' in runtime_source
    assert 'compile(patched_source, str(PATCHED), "exec")' in smoke_source


def test_person_smoke_covers_all_individual_pages() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    for label in (
        "Généralités",
        "Questionnaire",
        "Qualifications",
        "Contrats",
        "Présences",
        "Scénarios",
        "Frais",
        "Recrutement",
    ):
        assert f'"{label}"' in source

    assert "GetPageCount()" in source
    assert "SetSelection(_smoke_index)" in source
    assert "TEAMWORKS_SMOKE_PERSON_DIALOG_READY" in source
    assert "TEAMWORKS_SMOKE_PERSON_DIALOG_FAILED" in source
    assert "PATCHED.unlink(missing_ok=True)" in source
