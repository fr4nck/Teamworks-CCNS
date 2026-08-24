import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Ol" / "OL_entretiens.py"
CORE = ROOT / "teamworks" / "Ol" / "OL_entretiens_core.py"


def _src(path):
    return path.read_text(encoding="utf-8")


def test_interviews_list_shell_and_core_are_valid_python():
    ast.parse(_src(SHELL))
    ast.parse(_src(CORE))


def test_interviews_list_keeps_historical_crud_export_and_lock_engine():
    shell, core = _src(SHELL), _src(CORE)
    assert "OL_entretiens_core as CORE" in shell
    assert "class ListView(CORE.ListView):" in shell
    for method in ("Ajouter", "Modifier", "Supprimer", "Rechercher", "ExportExcel", "GestionVerrouillage"):
        assert "def %s" % method in core
    assert 'nom="password_entretien"' in shell


def test_interviews_list_uses_text_ratings_and_employee_marker():
    source = _src(SHELL)
    for label in ("Avis inconnu", "Pas convaincant", "Mitigé", "Bien", "Très bien", "Avis verrouillé"):
        assert label in source
    assert '_(u"salarié")' in source
    assert "Smiley_" not in source
    assert "imageGetter=" not in source
    assert "wx.RED" not in source


def test_interviews_list_has_no_floating_lock_or_legacy_colours():
    source = _src(SHELL)
    for legacy in ("StaticBitmap", "HyperLinkCtrl", "Tekton", "#EEF4FB", "Images/22x22", "Images/16x16"):
        assert legacy not in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert 'UTILS_Styles.GetFont("body-secondary")' in source


def test_interviews_lock_is_explicit_and_password_dialog_is_semantic():
    source = _src(SHELL)
    assert '_(u"Déverrouiller les avis")' in source
    assert '_(u"Verrouiller les avis")' in source
    assert "class SaisiePassword(wx.Dialog):" in source
    assert "CTRL_Section.Section(" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "compact")' in source
    assert 'style=wx.TE_PASSWORD' in source or 'wx.TE_PASSWORD | wx.TE_PROCESS_ENTER' in source
