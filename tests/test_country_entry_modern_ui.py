from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_pays.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_country_entry_uses_charter_components():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert ".Fit(self)" not in source
    assert "CTRL_Texte.H2" in source
    assert "CTRL_Texte.Label" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "compact")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("dialog_padding")' in source
    assert "CTRL_Bouton_image.CTRL" in source


def test_country_entry_keeps_persistence_and_validation():
    source = _source()
    assert 'DB.ReqInsert("pays", listeDonnees)' in source
    assert 'DB.ReqMAJ("pays", listeDonnees, "IDpays", self.IDpays)' in source
    assert '("code_drapeau", "autre")' in source
    assert 'if valeur == "":' in source
    assert 'FonctionsPerso.FrameOuverte("panel_config_pays")' in source
