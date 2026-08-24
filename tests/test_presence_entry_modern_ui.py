import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_presence_entry_is_valid_python():
    ast.parse(_source())


def test_presence_entry_uses_semantic_sections_and_typography():
    source = _source()
    assert "wx.StaticBox" not in source
    assert "wx.FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.Font(" not in source
    assert "PINK" not in source
    assert source.count("CTRL_Section.Section(") == 3
    assert 'titre=_(u"Dates et personnes")' in source
    assert 'titre=_(u"Horaires et légende")' in source
    assert 'titre=_(u"Catégorie")' in source
    assert 'UTILS_Styles.GetFont("data-large")' in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source


def test_presence_entry_category_tree_is_textual_not_rainbow():
    source = _source()
    assert "FormateCouleur" not in source
    assert "CreationImage" not in source
    assert "wx.ImageList" not in source
    assert "SetItemImage" not in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source
    assert 'UTILS_Interface.GetToken("on_surface")' in source


def test_presence_entry_uses_one_checkbox_implementation_on_phoenix():
    source = _source()
    assert '_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin' in source
    assert 'if _PHOENIX:\n            self.EnableCheckBoxes(True)\n        else:\n            CheckListCtrlMixin.__init__(self)' in source
    assert "IsItemChecked" in source
    assert "EVT_LIST_ITEM_CHECKED" in source
    assert "EVT_LIST_ITEM_UNCHECKED" in source
    assert "wx.SUNKEN_BORDER" not in source


def test_presence_entry_refreshes_selected_dates_instead_of_stale_reference():
    source = _source()
    assert "def CreationDictDonnees" in source
    assert 'if hasattr(self, "listCtrl_donnees"):' in source
    assert "self.listCtrl_donnees.SetDonnees(self.dictDonnees)" in source
    assert "def SetDonnees(self, dictDonnees):" in source
    assert "self.Remplissage()" in source
    assert "self.owner.UpdateSelectionSummary()" in source


def test_presence_entry_keeps_validation_and_persistence_contract():
    source = _source()
    for method in (
        "ValidationDonnees",
        "SauvegardeModif",
        "SauvegardeNouveau",
        "GetDonneesModele",
        "ImportPersonnes",
        "ImportDonneesModif",
    ):
        assert "def %s" % method in source
    assert 'DB.ReqMAJ("presences"' in source
    assert 'DB.ReqInsert(\n                "presences"' in source
    assert "UTILS_Presences.normaliser_intitule_presence" in source
