import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Ol" / "OL_candidatures.py"
CORE = ROOT / "teamworks" / "Ol" / "OL_candidatures_core.py"


def _src(path):
    return path.read_text(encoding="utf-8")


def test_applications_list_shell_and_core_are_valid_python():
    ast.parse(_src(SHELL))
    ast.parse(_src(CORE))


def test_applications_list_keeps_historical_engine():
    shell, core = _src(SHELL), _src(CORE)
    assert "OL_candidatures_core as CORE" in shell
    assert "class ListView(CORE.ListView):" in shell
    for method in ("Ajouter", "Modifier", "Supprimer", "Rechercher", "CourrierPublipostage", "ExportExcel"):
        assert "def %s" % method in core


def test_applications_list_replaces_images_with_business_text():
    source = _src(SHELL)
    assert "DEPOT_LABELS" in source
    assert "DECISION_LABELS" in source
    assert "REPONSE_LABELS" in source
    assert '_(u"salarié")' in source
    assert '_(u"À envoyer")' in source
    assert '_(u"Non requise")' in source
    assert "AddNamedImages" not in source
    assert "imageGetter=" not in source
    assert "Images/16x16" not in source
    assert "wx.RED" not in source


def test_applications_list_uses_only_charter_surfaces_and_font():
    source = _src(SHELL)
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert 'UTILS_Interface.GetToken("surface_container_low")' in source
    assert 'UTILS_Styles.GetFont("body-secondary")' in source
    assert "#EEF4FB" not in source
    assert "Tekton" not in source


def test_applications_context_menu_is_textual():
    source = _src(SHELL)
    assert "def OnContextMenu" in source
    for label in ("Ajouter", "Modifier", "Supprimer", "Créer un courrier ou un email", "Rechercher / filtrer", "Colonnes et options", "Exporter vers Excel"):
        assert label in source
    assert "SetBitmap" not in source
