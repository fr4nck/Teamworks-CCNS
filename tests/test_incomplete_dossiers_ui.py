import ast
from pathlib import Path


SOURCE = Path("teamworks/Ctrl/CTRL_Gadget_pb_personnes.py")


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_incomplete_dossiers_control_is_valid_python():
    ast.parse(_source())


def test_incomplete_dossiers_no_longer_uses_fixed_historical_layout():
    source = _source()
    assert "FonctionsPerso.BarreTitre" not in source
    assert "FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.BoxSizer" in source


def test_incomplete_dossiers_no_longer_forces_tiny_fonts_or_blue_fill():
    source = _source()
    assert "SetPointSize(7)" not in source
    assert "SetPointSize(8)" not in source
    assert "(122, 161, 230)" not in source
    assert "(179, 185, 231)" not in source


def test_incomplete_dossiers_uses_semantic_states():
    source = _source()
    for token in (
        "surface_container_lowest",
        "primary",
        "on_surface",
        "on_surface_variant",
        "outline_variant",
        "selection",
    ):
        assert 'GetToken("%s")' % token in source
