import ast
from pathlib import Path


FLOATING_PATH = Path("teamworks/Ctrl/CTRL_Gadgets_flottants.py")
GADGET_PATH = Path("teamworks/Gadget.py")
HOME_PATH = Path("teamworks/Ctrl/CTRL_Accueil.py")
STYLES_PATH = Path("teamworks/Utils/UTILS_Styles.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path))


def test_gadget_modules_are_valid_python():
    for path in (FLOATING_PATH, GADGET_PATH, HOME_PATH, STYLES_PATH):
        _tree(path)


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
    assert ".Row(index // colonnes)" in pane_builder
    assert ".Position(index % colonnes)" in pane_builder
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


def test_gadget_chrome_is_owned_by_the_component_and_uses_semantic_tokens():
    host = _source(FLOATING_PATH)
    gadget = _source(GADGET_PATH)
    assert "AppliquerThemeGadget" in host
    assert 'getattr(gadget, "AppliquerTheme", None)' in host
    assert "def AppliquerTheme(self):" in gadget
    assert 'GetToken("surface")' in gadget
    assert 'GetToken("surface_container_high")' in gadget
    assert 'GetToken("on_surface")' in gadget
    assert 'GetToken("outline_variant")' in gadget


def test_gadget_workspace_consumes_central_gadget_metrics():
    host = _source(FLOATING_PATH)
    styles = _source(STYLES_PATH)
    assert "GADGET_METRICS" in styles
    for metric in ("default_size", "min_size", "floating_min_size", "columns", "floating_origin", "floating_step"):
        assert '"%s"' % metric in styles
    assert "UTILS_Styles.GetGadgetMetric" in host
    assert "max(200" not in host
    assert "max(150" not in host
    assert ".Row(index // 3)" not in host
    assert ".Position(index % 3)" not in host


def test_home_defaults_consume_charter_without_overriding_user_content_options():
    home = _source(HOME_PATH)
    assert 'GADGET_DEFAULT_SIZE = UTILS_Styles.GetGadgetMetric("default_size", scaled=False)' in home
    assert '"taille": GADGET_DEFAULT_SIZE' in home
    assert '_literal(taille, GADGET_DEFAULT_SIZE)' in home
    assert '"nomPolice": "Segoe Print"' in home
    assert "Personnalisation du contenu du gadget" in home


def test_gadget_chrome_no_longer_uses_historical_fixed_paint_layout():
    source = _source(GADGET_PATH)
    panel = source.split("class PanelGadget", 1)[1].split("class Gadget_BlocNotes", 1)[0]
    assert "FlexGridSizer" not in panel
    assert ".Fit(" not in panel
    assert "GradientFillLinear" not in panel
    assert "wx.Font(8" not in panel
    assert "wx.BoxSizer" in panel
    assert "wx.StaticText" in panel
    assert "EVT_BUTTON" in panel


def test_home_screen_uses_floating_workspace_instead_of_html_layout():
    source = _source(HOME_PATH)
    assert "from Ctrl import CTRL_Gadgets_flottants" in source
    assert "class MyHtmlWindow(CTRL_Gadgets_flottants.EspaceGadgets)" in source
    assert "wxp module=\"Gadget\"" not in source
    assert 'UTILS_Interface.GetToken("surface")' in source


def test_home_dashboard_owns_the_full_work_surface():
    source = _source(HOME_PATH)
    panel = source.split("class Panel(wx.Panel):", 1)[1].split("class AffichageGadgets", 1)[0]
    assert "Logo_accueil.png" not in panel
    assert "FlexGridSizer" not in panel
    assert "wx.BoxSizer(wx.VERTICAL)" in panel
    assert "sizer.Add(self.html, 1, wx.EXPAND)" in panel


def test_home_refresh_does_not_double_freeze_aui():
    source = _source(HOME_PATH)
    maj = source.split("def MAJ_Gadgets", 1)[1].split("def MAJpanel", 1)[0]
    assert "Freeze(" not in maj
    assert "Thaw(" not in maj
    assert "self.html.MAJ(self.listeGadgets)" in maj


def test_home_parses_persisted_gadgets_without_eval():
    source = _source(HOME_PATH)
    assert "ast.literal_eval" in source
    assert "eval(" not in source.replace("literal_eval(", "")


def test_floating_workspace_keeps_gadget_business_contract():
    source = _source(FLOATING_PATH)
    assert "Gadget.PanelGadget(" in source
    assert "Fermer_Gadget" in source
    assert "Ouvre_Gadget" in source
    assert "gadget.SaveConfig" in source


def test_hiding_one_gadget_does_not_rebuild_every_gadget():
    source = _source(FLOATING_PATH)
    maj = source.split("def MAJ(self, listeGadgets=None):", 1)[1].split("def Fermer_Gadget", 1)[0]
    assert "existants - souhaites" in maj
    assert "souhaites - existants" in maj
    assert "_SupprimerGadget" in maj
    assert "_CreerGadget" in maj
    assert "self.Construire()" not in maj.split("if self.manager is None:", 1)[1].split("visibles =", 1)[1]


def test_closing_gadget_repaints_before_persistence():
    source = _source(FLOATING_PATH)
    fermer = source.split("def Fermer_Gadget", 1)[1].split("def Ouvre_Gadget", 1)[0]
    hide_pos = fermer.index("pane.Hide()")
    update_pos = fermer.index("self.manager.Update()")
    persist_pos = fermer.index("self.PlanifierVisibilite")
    assert hide_pos < update_pos < persist_pos
    assert "gadget.SaveConfig" not in fermer
    assert "self.Construire()" not in fermer


def test_visibility_and_perspective_writes_are_deferred_and_deduplicated():
    source = _source(FLOATING_PATH)
    assert "def PlanifierVisibilite" in source
    assert "wx.CallLater(" in source
    assert "def PlanifierSauvegardePerspective" in source
    assert "self._timer_perspective.Stop()" in source
    assert "self._timers_visibilite" in source


def test_opening_one_missing_gadget_does_not_rebuild_dashboard():
    source = _source(FLOATING_PATH)
    ouvrir = source.split("def Ouvre_Gadget", 1)[1].split("def OnPaneClose", 1)[0]
    assert "_CreerGadget" in ouvrir
    assert "PlanifierVisibilite" in ouvrir
    assert "self.Construire()" not in ouvrir
    assert "DetachPane" in source
