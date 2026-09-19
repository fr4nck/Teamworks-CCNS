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


def test_persons_splitter_starts_proportional_then_stays_user_controlled():
    source = _source()
    init = source.split("def InitialiserSeparateur", 1)[1].split(
        "def OnBoutonAjouter", 1
    )[0]

    assert "GetClientSize().GetWidth()" in init
    assert "largeur * 0.18" in init
    assert "max(220, min(360" in init
    assert "self._separateur_initialise = True" in init


def test_persons_actions_use_the_common_scaled_button_contract():
    source = _source()
    assert "_bouton_action" in source
    assert "CTRL_Bouton_image.CTRL(" in source
    assert 'Chemins.GetStaticPath("Images/32x32/%s" % nom_image)' in source
    assert "wx.BitmapButton(" not in source
    assert "SetMinSize((cote, cote))" not in source
    assert '"echelle_interface"' not in source
    assert '"echelle_police"' not in source


def test_persons_list_keeps_stable_user_controlled_columns():
    source = _source()
    assert "AjusterColonnes" not in source
    assert "listCtrl_personnes.Bind(wx.EVT_SIZE" not in source
    assert "SetColumnWidth" not in source
    assert 'view_id="personnes.main"' in source


def test_persons_screen_uses_semantic_surfaces_instead_of_blue_fill():
    source = _source()
    assert 'GetToken("surface")' in source
    assert 'GetToken("surface_container_lowest")' in source
    assert 'GetToken("surface_container_low")' in source
    assert "(122, 161, 230)" not in source
    assert "(214, 223, 247)" not in source
