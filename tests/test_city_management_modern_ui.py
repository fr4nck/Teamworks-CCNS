import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Gestion_villes.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_city_management_is_valid_python():
    ast.parse(_source())


def test_city_management_uses_semantic_search_layout():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert ".Fit(self)" not in source
    assert "wx.BitmapButton" not in source
    assert "CTRL_Texte.H1" in source
    assert source.count("CTRL_Section.Section(") == 2
    assert 'titre=_(u"Recherche")' in source
    assert 'titre=_(u"Saisie manuelle")' in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source


def test_city_results_use_available_width_without_old_blue_stripes():
    source = _source()
    assert "def AjusterColonnes" in source
    assert "largeur * 0.25" in source
    assert 'attr1.SetBackgroundColour("#EEF4FB")' not in source
    assert "def OnGetItemAttr(self, item):\n        return None" in source
    assert 'UTILS_Styles.GetIconSize("small")' in source


def test_city_management_keeps_search_and_export_contract():
    source = _source()
    assert "UTILS_Phonex.phonex" in source
    assert 'self.criteres = "WHERE phonex(ville)=phonex(?)"' in source
    assert "def RechercheBase" in source
    assert "def ExportManuelVille" in source
    assert "def ExportListeVille" in source
    assert 'self.parent.text_cp_naiss.SetValue' in source
    assert 'self.parent.text_ville.SetValue' in source
    assert "OnItemActivated" in source


def test_city_list_finds_dialog_by_ancestor_not_fixed_parent_depth():
    source = _source()
    assert "self.dialog = parent" in source
    assert "while self.dialog is not None and not isinstance(self.dialog, Dialog):" in source
    assert "self.dialog = self.dialog.GetParent()" in source
    assert "self.GetGrandParent().exportCP" not in source
    assert "self.dialog.ExportListeVille" in source
