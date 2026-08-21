from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_coords.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_contact_details_dialog_has_no_legacy_card_grid():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert "wx.StaticBoxSizer" not in source
    assert "wx.BitmapButton" not in source
    assert "Images/16x16/" not in source
    assert ".Fit(self)" not in source
    assert "wx.ToggleButton" in source
    assert "wx.WrapSizer" in source


def test_contact_category_selection_uses_semantic_states():
    source = _source()
    assert 'UTILS_Interface.GetToken("primary_container")' in source
    assert 'UTILS_Interface.GetToken("on_primary_container")' in source
    assert 'UTILS_Interface.GetToken("surface_container_low")' in source
    assert "_select_category" in source
    assert "FromDIP" in source


def test_contact_details_keep_normalization_and_persistence_contract():
    source = _source()
    assert "normaliser_email" in source
    assert "normaliser_telephone" in source
    assert "normaliser_texte" in source
    assert "DB.ReqInsert(self.nomTable, listeDonnees)" in source
    assert 'DB.ReqMAJ(self.nomTable, listeDonnees, "IDcoord", self.IDcoord)' in source
