from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "tools" / "smoke_parameter_dialogs.py"
ENTRYPOINT = ROOT / "teamworks" / "Teamworks.py"
CORE = ROOT / "teamworks" / "Teamworks_core.py"


def test_parameter_smoke_targets_real_teamworks_entrypoint() -> None:
    source = SMOKE.read_text(encoding="utf-8")
    entrypoint_source = ENTRYPOINT.read_text(encoding="utf-8")
    core_source = CORE.read_text(encoding="utf-8")
    marker = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'

    assert marker in core_source
    assert "import Teamworks_core as CORE" in entrypoint_source
    assert f"MARKER_LINE = '{marker}'" in source
    assert 'PATCHED = TEAMWORKS_DIR / "Teamworks_parameter_dialogs_smoke.py"' in source
    assert 'PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_parameter_dialogs_smoke.py"' in source
    assert "import Teamworks_core_parameter_dialogs_smoke as CORE" in source
    assert 'timeout=240' in source
    assert "PATCHED.unlink(missing_ok=True)" in source
    assert "PATCHED_CORE.unlink(missing_ok=True)" in source


def test_parameter_smoke_rejects_blank_dialogs() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    for marker in (
        "GetClientSize()",
        "GetChildren()",
        "IsShownOnScreen()",
        "contenu non construit",
        "aucun contrôle visible",
        "TEAMWORKS_SMOKE_PARAMETER_DIALOGS_READY",
        "TEAMWORKS_SMOKE_PARAMETER_DIALOGS_FAILED",
    ):
        assert marker in source


def test_parameter_smoke_covers_clickable_parameter_families() -> None:
    source = SMOKE.read_text(encoding="utf-8")

    for label in (
        "Questionnaires",
        "Qualifications",
        "Types de pièces",
        "Situations",
        "Pays",
        "Catégories de présences",
        "Classifications",
        "Champs de contrats",
        "Modèles de contrats",
        "Types de contrats",
        "Valeurs de points",
        "Protection des entretiens",
        "Fonctions",
        "Affectations",
        "Diffuseurs",
        "Offres d'emploi",
        "Vacances",
        "Jours fériés",
    ):
        assert f'("{label}",' in source
