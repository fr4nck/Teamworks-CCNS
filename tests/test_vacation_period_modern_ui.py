from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_periode_vacances.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_vacation_period_dialog_has_no_rigid_legacy_shell():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert "wx.StaticBox" not in source
    assert "wx.StaticBoxSizer" not in source
    assert ".Fit(self)" not in source
    assert "Images/16x16/" not in source
    assert "wx.BoxSizer" in source
    assert "AddStretchSpacer" in source


def test_vacation_period_dialog_consumes_graphic_charter():
    source = _source()
    assert 'UTILS_Interface.GetToken("surface")' in source
    assert "CTRL_Texte.H2" in source
    assert "CTRL_Texte.Label" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "compact")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("dialog_padding")' in source
    assert "FromDIP" not in source
    assert "SetPointSize" not in source


def test_vacation_period_keeps_persistence_and_validation_contract():
    source = _source()
    assert 'DB.ReqInsert("periodes_vacances"' in source
    assert 'DB.ReqMAJ("periodes_vacances"' in source
    assert "if date_debut > date_fin" in source
    assert 'FonctionsPerso.FrameOuverte("panel_config_periodes_vacs")' in source
