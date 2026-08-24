import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = (
    ("OL_candidats.py", "OL_candidats_core.py"),
    ("OL_emplois.py", "OL_emplois_core.py"),
)


def _src(name):
    return (ROOT / "teamworks" / "Ol" / name).read_text(encoding="utf-8")


def test_candidates_and_jobs_shells_and_cores_are_valid_python():
    for shell, core in PAIRS:
        ast.parse(_src(shell))
        ast.parse(_src(core))


def test_candidates_and_jobs_keep_historical_engines():
    assert "class ListView(CORE.ListView):" in _src("OL_candidats.py")
    assert "class ListView(CORE.ListView):" in _src("OL_emplois.py")
    for core in ("OL_candidats_core.py", "OL_emplois_core.py"):
        source = _src(core)
        for method in ("Ajouter", "Modifier", "Supprimer", "Rechercher", "ExportExcel"):
            assert "def %s" % method in source


def test_candidates_list_drops_redundant_civility_icons_and_blue_zebra():
    source = _src("OL_candidats.py")
    assert "AddNamedImages" not in source
    assert "imageGetter=" not in source
    assert "Homme.png" not in source
    assert "Femme.png" not in source
    assert "#EEF4FB" not in source
    assert "Tekton" not in source
    assert "if args == \"image_civilite\" and not self.activeCheckBoxes" in source


def test_candidates_menu_is_textual_and_keeps_both_mail_paths():
    source = _src("OL_candidats.py")
    assert "def _mail_interne" in source
    assert "def _mail_systeme" in source
    for label in ("Créer un courrier ou un email", "Rechercher / filtrer", "Colonnes et options", "Exporter vers Excel"):
        assert label in source
    assert "SetBitmap" not in source


def test_jobs_list_uses_semantic_surfaces_and_correct_application_count_key():
    source = _src("OL_emplois.py")
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert 'UTILS_Styles.GetFont("body-secondary")' in source
    assert "#EEF4FB" not in source
    assert "Tekton" not in source
    assert "SELECT IDemploi, COUNT(IDcandidature)" in source
    assert "GROUP BY IDemploi" in source


def test_jobs_menu_is_textual():
    source = _src("OL_emplois.py")
    for label in ("Ajouter", "Modifier", "Supprimer", "Rechercher / filtrer", "Colonnes et options", "Exporter vers Excel"):
        assert label in source
    assert "SetBitmap" not in source
