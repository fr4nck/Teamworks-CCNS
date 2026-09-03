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
    assert "wx.ToggleButton(" not in source
    assert "CTRL_Bouton_image.Toggle" in source
    assert "wx.WrapSizer" in source


def test_contact_category_selection_uses_common_semantic_button_contract():
    source = _source()
    assert "CTRL_Bouton_image.Toggle" in source
    assert "_select_category" in source
    assert "button.SetValue(categorie == self.categorieSelect)" in source
    assert "CTRL_Texte.H3" in source
    assert "CTRL_Texte.Label" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "fit")' in source
    assert "UTILS_Styles.RefitWindow(self, centre=False)" in source
    assert 'UTILS_Styles.GetLayoutSpacing("dialog_padding")' in source
    assert "FromDIP" not in source
    assert "SetPointSize" not in source


def test_contact_details_keep_normalization_and_persistence_contract():
    source = _source()
    assert "normaliser_email" in source
    assert "normaliser_telephone" in source
    assert "normaliser_texte" in source
    assert "DB.ReqInsert(self.nomTable, listeDonnees)" in source
    assert 'DB.ReqMAJ(self.nomTable, listeDonnees, "IDcoord", self.IDcoord)' in source
