import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Saisie_entretien.py"


def _source():
    return DIALOG.read_text(encoding="utf-8")


def test_interview_dialog_is_valid_python():
    ast.parse(_source())


def test_interview_dialog_uses_semantic_layout():
    source = _source()
    assert "wx.StaticBox" not in source
    assert "wx.FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.BitmapButton" not in source
    assert "CTRL_Section.Section(" in source
    assert "CTRL_Texte.Label" in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source


def test_interview_dialog_uses_charter_for_validation_and_typography():
    source = _source()
    assert 'invalidBackgroundColour=UTILS_Interface.GetToken("danger")' in source
    assert 'UTILS_Styles.GetFont("data-large")' in source
    assert "PINK" not in source
    assert "wx.Font(" not in source


def test_interview_dialog_keeps_rating_indexes_without_decorative_images():
    source = _source()
    assert "class MyBitmapComboBox(wx.Choice):" in source
    assert "Smiley_" not in source
    for label in ("Avis inconnu", "Pas convaincant", "Mitigé", "Bien", "Très bien"):
        assert label in source
    assert "self.ctrl_avis.GetSelection()" in source
    assert "self.ctrl_avis.SetSelection(avis)" in source


def test_interview_dialog_keeps_database_contract_and_robust_parent_refresh():
    source = _source()
    assert 'DB.ReqInsert("entretiens"' in source
    assert 'DB.ReqMAJ("entretiens"' in source
    assert 'def _ancestor_named(window, name):' in source
    assert '_ancestor_named(parent, "Recrutement")' in source
    assert '_ancestor_named(parent, "panel_resume")' in source
