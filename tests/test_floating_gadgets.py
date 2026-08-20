import ast
from pathlib import Path


FLOATING_PATH = Path("teamworks/Ctrl/CTRL_Gadgets_flottants.py")
HOME_PATH = Path("teamworks/Ctrl/CTRL_Accueil.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path))


def test_floating_gadgets_module_is_valid_python():
    _tree(FLOATING_PATH)


def test_floating_workspace_uses_native_aui_capabilities():
    source = _source(FLOATING_PATH)

    assert "import wx.aui as aui" in source
    assert ".Float()" in source
    assert ".Floatable(True)" in source
    assert ".Dockable(True)" in source
    assert ".Movable(True)" in source
    assert ".Resizable(True)" in source
    assert ".Gripper(True)" in source


def test_floating_workspace_persists_its_perspective():
    source = _source(FLOATING_PATH)

    assert "SavePerspective" in source
    assert "LoadPerspective" in source
    assert 'PERSPECTIVE_KEY = "gadgets_perspective"' in source
    assert "ReinitialiserDisposition" in source


def test_home_screen_uses_floating_workspace_instead_of_html_layout():
    source = _source(HOME_PATH)

    assert "from Ctrl import CTRL_Gadgets_flottants" in source
    assert "class MyHtmlWindow(CTRL_Gadgets_flottants.EspaceGadgets)" in source
    assert "wxp module=\"Gadget\"" not in source
    assert 'UTILS_Interface.GetToken("surface")' in source


def test_floating_workspace_keeps_legacy_gadget_contract():
    source = _source(FLOATING_PATH)

    assert "Gadget.PanelGadget(" in source
    assert "Fermer_Gadget" in source
    assert "Ouvre_Gadget" in source
    assert "gadget.SaveConfig" in source
