import ast
from pathlib import Path


SOURCE = Path("teamworks/Ctrl/CTRL_Dossiers_incomplets_ccns_helper.py")


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_ccns_helper_is_valid_python():
    ast.parse(_source())


def test_ccns_helper_uses_semantic_status_tokens():
    source = _source()

    assert 'GetToken("danger")' in source
    assert 'GetToken("warning")' in source
    assert 'GetToken("success")' in source
    assert "wx.Colour(150, 0, 0)" not in source
    assert "wx.Colour(130, 80, 0)" not in source
    assert "wx.Colour(0, 110, 0)" not in source


def test_contract_dialog_follows_available_display():
    source = _source()

    assert "wx.Display.GetFromWindow(parent)" in source
    assert "zone.GetWidth() * 0.82" in source
    assert "zone.GetHeight() * 0.82" in source
    assert "dlg.SetSize(_taille_dialogue(parent))" in source
    assert "dlg.SetSize((980, 720))" not in source
