from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Config_situations.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_social_situations_use_semantic_direct_layout():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert ".Fit(self)" not in source
    assert "CTRL_Texte.H2" in source
    assert "CTRL_Texte.BodySecondary" in source
    assert "wx.WrapSizer" in source
    assert 'UTILS_Interface.GetToken("surface")' in source
    assert 'UTILS_Interface.GetToken("surface_container_lowest")' in source


def test_social_situations_actions_and_window_follow_charter():
    source = _source()
    assert "wx.BitmapButton" not in source
    assert "CTRL_Bouton_image.CTRL" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("content_padding")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("field_gap")' in source


def test_social_situations_keep_business_contract():
    source = _source()
    assert 'DB.ReqInsert("situations"' in source
    assert 'DB.ReqMAJ(' in source and '"situations"' in source
    assert 'DB.ReqDEL("situations", "IDsituation", IDsituation)' in source
    assert "Count(personnes.IDpersonne)" in source
    assert "nbreTitulaires != 0" in source
    assert "def AjusterColonnes" in source
