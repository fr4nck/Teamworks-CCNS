from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Config_pays.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_countries_use_semantic_direct_layout():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert ".Fit(self)" not in source
    assert "wx.BitmapButton" not in source
    assert "CTRL_Texte.H2" in source
    assert "CTRL_Texte.BodySecondary" in source
    assert "wx.WrapSizer" in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source


def test_countries_table_is_responsive_and_keeps_flags_as_content():
    source = _source()
    assert "def AjusterColonnes" in source
    assert 'UTILS_Styles.GetIconSize("medium")' in source
    assert "Images/Drapeaux/" in source
    assert 'SetColumnWidth(1, 0)' in source
    assert "getattr(self, \"imgDrapeau%s\" % IDvaleur" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source


def test_countries_keep_business_guards_and_selection_contract():
    source = _source()
    assert 'DB.ReqDEL("pays", "IDpays", ID)' in source
    assert "if ID <= 230" in source
    assert "GetNbTitulaires" in source
    assert 'self.parent.SetPaysNaiss(IDpays=self.panel_contenu.listCtrl.selection)' in source
    assert 'self.parent.SetNationalite(IDpays=self.panel_contenu.listCtrl.selection)' in source
