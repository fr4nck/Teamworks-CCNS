import ast
from pathlib import Path


SOURCE = Path("teamworks/Ctrl/CTRL_Personnes.py")


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_persons_screen_is_valid_python():
    ast.parse(_source())


def test_persons_screen_no_longer_uses_historical_layout_fillers():
    source = _source()
    assert "MultiSplitterWindow" not in source
    assert "panel_vide" not in source
    assert "PanelArrondi" not in source
    assert "FlexGridSizer" not in source


def test_persons_screen_uses_native_flexible_layout():
    source = _source()
    assert "wx.SplitterWindow" in source
    assert "wx.BoxSizer" in source
    assert "wx.WrapSizer" in source
    assert "SetMinimumPaneSize(180)" in source
    assert "SetSashGravity(0.0)" in source


def test_persons_actions_scale_directly_in_the_screen():
    source = _source()
    assert "_bouton_action" in source
    assert "wx.IMAGE_QUALITY_HIGH" in source
    assert "SetMinSize((cote, cote))" in source
    assert '"echelle_police"' in source


def test_persons_list_consumes_available_width_directly():
    source = _source()
    assert "AjusterColonnes" in source
    assert "GetClientSize().GetWidth()" in source
    assert "SetColumnWidth" in source
    assert "largeur_dispo > total" in source


def test_persons_screen_uses_semantic_surfaces_instead_of_blue_fill():
    source = _source()
    assert 'GetToken("surface")' in source
    assert 'GetToken("surface_container_lowest")' in source
    assert 'GetToken("surface_container_low")' in source
    assert "(122, 161, 230)" not in source
    assert "(214, 223, 247)" not in source
