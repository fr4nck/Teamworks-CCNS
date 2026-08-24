import ast
from pathlib import Path


SOURCE = Path("teamworks/Ctrl/CTRL_Gadget_CCNS.py")


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_ccns_gadget_is_valid_python():
    ast.parse(_source())


def test_ccns_gadget_uses_semantic_status_colours():
    source = _source()

    assert 'GetToken("danger")' in source
    assert 'GetToken("warning")' in source
    assert 'GetToken("success")' in source
    assert 'GetToken("surface_container_low")' in source
    assert "wx.Colour(255, 228, 228)" not in source
    assert "wx.Colour(255, 245, 204)" not in source
    assert "wx.Colour(0, 110, 0)" not in source


def test_ccns_gadget_uses_flexible_columns_and_native_layout():
    source = _source()

    assert "UTILS_Colonnes.ColonnesFlexibles" in source
    assert "extensibles=(0,)" in source
    assert "extensibles=(0, 1)" in source
    assert "wx.WrapSizer" in source
    assert "wx.StaticBoxSizer" not in source
    assert "wx.BORDER_SUNKEN" not in source
