from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_feries_auto.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_auto_holidays_dialog_has_no_rigid_legacy_layout():
    source = _source()
    assert "wx.FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.BoxSizer" in source
    assert "AddStretchSpacer" in source


def test_auto_holidays_dialog_consumes_semantic_charter():
    source = _source()
    assert 'UTILS_Interface.GetToken("surface")' in source
    assert "CTRL_Texte.BodySecondary" in source
    assert "CTRL_Texte.H2" in source
    assert "CTRL_Texte.Label" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "compact")' in source
    assert 'UTILS_Styles.GetLayoutSpacing("dialog_padding")' in source
    assert "FromDIP" not in source
    assert ".Wrap(" in source


def test_auto_holidays_keeps_business_calculation_contract():
    source = _source()
    assert "easter(annee)" in source
    assert "relativedelta(days=+1)" in source
    assert "relativedelta(days=+39)" in source
    assert "relativedelta(days=+50)" in source
    assert 'DB.ReqInsert("jours_feries"' in source
