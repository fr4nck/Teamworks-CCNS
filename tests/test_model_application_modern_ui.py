import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Dlg" / "DLG_Application_modele.py"
CORE = ROOT / "teamworks" / "Dlg" / "DLG_Application_modele_core.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_model_application_shell_and_core_are_valid_python():
    ast.parse(_source(SHELL))
    ast.parse(_source(CORE))


def test_model_application_keeps_business_engine_isolated():
    shell = _source(SHELL)
    core = _source(CORE)
    assert "from Dlg import DLG_Application_modele_core as CORE" in shell
    assert "class Panel(CORE.Panel):" in shell
    assert "def OnBoutonOk" in core
    assert "def Importation_Jours_Vacances" in core
    assert "def Importation_Feries" in core
    assert "DLG_Confirm_appli_modele.Dialog" in core
    assert 'DB.ReqInsert("presences"' in core


def test_model_application_shell_uses_semantic_sections_and_buttons():
    source = _source(SHELL)
    assert "wx.StaticBox" not in source
    assert "wx.BitmapButton" not in source
    assert "wx.FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert source.count("CTRL_Section.Section(") == 2
    assert 'titre=_(u"Période et personnes")' in source
    assert 'titre=_(u"Modèles")' in source
    assert "CTRL_Bouton_image.CTRL" in source
    assert "wx.WrapSizer" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in source


def test_model_application_lists_use_one_checkbox_implementation():
    source = _source(SHELL)
    assert '_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin' in source
    assert source.count("self.EnableCheckBoxes(True)") == 2
    assert source.count("CheckListCtrlMixin.__init__(self)") == 2
    assert source.count("EVT_LIST_ITEM_CHECKED") == 2
    assert source.count("EVT_LIST_ITEM_UNCHECKED") == 2
    assert "wx.SUNKEN_BORDER" not in source


def test_model_application_keeps_selection_and_model_management_contract():
    source = _source(SHELL)
    assert "self.owner.selectionPersonnes[:] = selection" in source
    assert "self.selections = [" in source
    assert "self.owner.OnBoutonAjouter(None)" in source
    assert "self.owner.OnBoutonModifier(None)" in source
    assert "self.owner.OnBoutonDupliquer(None)" in source
    assert "self.owner.OnBoutonSupprimer(None)" in source
    assert "def SetLabelRadio1" in source
    assert "def Fermer" in source
