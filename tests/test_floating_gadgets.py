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


def test_gadgets_start_visible_and_docked_instead_of_forced_floating():
    source = _source(FLOATING_PATH)
    pane_builder = source.split("def _info_pane", 1)[1].split("def _CreerGadget", 1)[0]

    assert ".Top()" in pane_builder
    assert ".Row(index // 3)" in pane_builder
    assert ".Position(index % 3)" in pane_builder
    assert ".Float()" not in pane_builder


def test_floating_workspace_persists_versioned_perspective():
    source = _source(FLOATING_PATH)

    assert "SavePerspective" in source
    assert "LoadPerspective" in source
    assert 'PERSPECTIVE_KEY = "gadgets_perspective_v2"' in source
    assert "ReinitialiserDisposition" in source


def test_floating_workspace_has_recovery_commands():
    source = _source(FLOATING_PATH)

    assert "ToutRendreFlottant" in source
    assert "ToutAncrer" in source
    assert "OnContextMenu" in source
    assert "Tout rendre flottant" in source
    assert "Tout ancrer dans l'accueil" in source
    assert "Réinitialiser la disposition" in source


def test_floating_gadget_chrome_uses_semantic_tokens():
    source = _source(FLOATING_PATH)

    assert "AppliquerThemeGadget" in source
    assert 'self._token_tuple("surface")' in source
    assert 'self._token_tuple("surface_container_highest")' in source
    assert 'self._token_tuple("surface_container_high")' in source
    assert 'self._token_tuple("outline_variant")' in source
    assert 'self._token_tuple("on_surface")' in source


def test_custom_gadget_content_colours_are_not_overwritten_blindly():
    source = _source(FLOATING_PATH)

    assert 'getattr(gadget, "couleurFondCadre", None) == (214, 223, 247)' in source
    assert 'gadget.couleurFondCadre = self._token_tuple("surface_container_low")' in source


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


def test_hiding_one_gadget_does_not_rebuild_every_gadget():
    source = _source(FLOATING_PATH)
    maj = source.split("def MAJ(self, listeGadgets=None):", 1)[1].split(
        "def Fermer_Gadget", 1
    )[0]

    assert "existants - souhaites" in maj
    assert "souhaites - existants" in maj
    assert "_SupprimerGadget" in maj
    assert "_CreerGadget" in maj
    assert "self.Construire()" not in maj.split("if self.manager is None:", 1)[1].split("visibles =", 1)[1]


def test_opening_one_missing_gadget_does_not_rebuild_dashboard():
    source = _source(FLOATING_PATH)
    ouvrir = source.split("def Ouvre_Gadget", 1)[1].split("def OnPaneClose", 1)[0]

    assert "_CreerGadget" in ouvrir
    assert "self.Construire()" not in ouvrir
    assert "DetachPane" in source
