import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Dlg" / "DLG_Config_fonctions.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Config_fonctions_core.py"


def _src(path):
    return path.read_text(encoding="utf-8")


def test_functions_reference_is_valid_python():
    ast.parse(_src(SHELL))
    ast.parse(_src(CORE))


def test_functions_reference_keeps_business_rules_in_core():
    shell, core = _src(SHELL), _src(CORE)
    assert "DLG_Config_fonctions_core as CORE" in shell
    assert "class Panel(CORE.Panel):" in shell
    for method in ("Ajouter", "Modifier", "Supprimer"):
        assert "def %s" % method in core
    assert "cand_fonctions" in core


def test_functions_reference_uses_semantic_table_and_actions():
    source = _src(SHELL)
    assert "CTRL_Section.Section(" in source
    assert 'titre=_(u"Fonctions de recrutement")' in source
    assert 'texte=_(u"Ajouter")' in source
    assert 'texte=_(u"Modifier")' in source
    assert 'texte=_(u"Supprimer")' in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source
    for legacy in ("wx.BitmapButton", "wx.FlexGridSizer", ".Fit(self)", "wx.ImageList", "#EEF4FB", "Images/16x16"):
        assert legacy not in source


def test_functions_reference_keeps_usage_count():
    source = _src(SHELL)
    assert 'COUNT(cand_fonctions.IDcand_fonction)' in source
    assert 'self.InsertColumn(2, _(u"Candidatures"))' in source
