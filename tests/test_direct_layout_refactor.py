import ast
from pathlib import Path


ROOT = Path("teamworks")
CUSTOMIZE = ROOT / "Utils" / "UTILS_Customize.py"
STYLES = ROOT / "Utils" / "UTILS_Styles.py"
PERSONS = ROOT / "Ctrl" / "CTRL_Personnes.py"
CONTRACTS = ROOT / "Ctrl" / "CTRL_Page_contrats_core.py"
PERSON_DIALOG = ROOT / "Dlg" / "DLG_Fiche_individuelle.py"
BUTTON = ROOT / "Ctrl" / "CTRL_Bouton_image.py"
GADGET = ROOT / "Gadget.py"
HOME = ROOT / "Ctrl" / "CTRL_Accueil.py"
NAVIGATION = ROOT / "Ctrl" / "CTRL_Navigation_principale.py"
RESPONSIVE = ROOT / "Utils" / "UTILS_Responsive.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def _called_names(path):
    tree = ast.parse(_source(path))
    return {
        name
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for name in [_dotted_name(node.func)]
        if name
    }


def test_refactored_sources_are_valid_python():
    for path in (
        CUSTOMIZE,
        STYLES,
        PERSONS,
        CONTRACTS,
        PERSON_DIALOG,
        BUTTON,
        GADGET,
        HOME,
        NAVIGATION,
    ):
        ast.parse(_source(path))


def test_no_runtime_responsive_overlay_is_installed():
    source = _source(CUSTOMIZE)
    assert not RESPONSIVE.exists()
    assert "UTILS_Responsive" not in source
    assert "install_auto_layout" not in source


def test_persons_layout_is_direct_and_flexible():
    source = _source(PERSONS)
    assert "MultiSplitterWindow" not in source
    assert "panel_vide" not in source
    assert "FlexGridSizer" not in source
    assert "wx.SplitterWindow" in source
    assert "wx.WrapSizer" in source
    assert "AjusterColonnes" in source
    assert "InitialiserSeparateur" in source


def test_contracts_layout_is_direct_and_flexible():
    source = _source(CONTRACTS)
    assert "FlexGridSizer" not in source
    assert "StaticBoxSizer" not in source
    assert "size=(250, -1)" not in source
    assert "wx.WrapSizer" in source
    assert "AjusterColonnes" in source
    assert "disponible - fixes" in source


def test_person_dialog_uses_available_display_instead_of_fit():
    source = _source(PERSON_DIALOG)
    assert "FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.Display.GetFromWindow" in source
    assert "zone.GetWidth() * 0.78" in source
    assert "zone.GetHeight() * 0.82" in source
    assert "wx.BoxSizer" in source
    assert ".Wrap(largeur)" in source


def test_scale_configuration_is_centralized_in_styles():
    styles = _source(STYLES)
    assert '"echelle_interface"' in styles
    assert '"echelle_police"' in styles
    assert styles.index('"echelle_interface"') < styles.index('"echelle_police"')
    assert "ajouter_si_manquant=False" in styles

    button = _source(BUTTON)
    assert "UTILS_Customize" not in button
    assert "UTILS_Styles.Scale" in button
    assert "UTILS_Styles.GetControlMetric" in button


def test_legacy_components_still_read_interface_scale_before_fallback():
    for path in (PERSONS, CONTRACTS, GADGET, NAVIGATION):
        source = _source(path)
        assert '"echelle_interface"' in source
        assert '"echelle_police"' in source
        assert source.index('"echelle_interface"') < source.index('"echelle_police"')
        assert "ajouter_si_manquant=False" in source


def test_icons_scale_in_components_without_global_patch():
    persons = _source(PERSONS)
    contracts = _source(CONTRACTS)
    dialog = _source(PERSON_DIALOG)
    button = _source(BUTTON)
    navigation = _source(NAVIGATION)

    assert "wx.IMAGE_QUALITY_HIGH" in persons
    assert "wx.IMAGE_QUALITY_HIGH" in contracts
    assert "wx.IMAGE_QUALITY_HIGH" in dialog
    assert 'UTILS_Styles.ICON_SIZES["medium"]' in button
    assert 'GetControlMetric("button_min_height")' in button
    assert "wx.IMAGE_QUALITY_HIGH" in navigation


def test_gadget_chrome_is_direct_not_runtime_repaint_overlay():
    source = _source(GADGET)
    panel = source.split("class PanelGadget", 1)[1].split(
        "class Gadget_BlocNotes", 1
    )[0]

    assert "wx.BoxSizer" in panel
    assert "FlexGridSizer" not in panel
    assert "GradientFillLinear" not in panel
    assert ".Fit(" not in panel
    assert "wx.StaticText" in panel
    assert "EVT_BUTTON" in panel


def test_home_uses_all_available_space_without_historical_logo_strip():
    source = _source(HOME)
    assert "Logo_accueil.png" not in source
    assert "FlexGridSizer" not in source
    assert "sizer.Add(self.html, 1, wx.EXPAND)" in source


def test_new_navigation_is_a_direct_replacement_component():
    source = _source(NAVIGATION)
    calls = _called_names(NAVIGATION)
    assert "wx.Toolbook" not in calls
    assert "wx.Simplebook" not in calls
    assert "wx.WrapSizer(" in source
    assert "wx.REMOVE_LEADING_SPACES" in source
    assert "class BoutonNavigation(wx.Control)" in source
    assert "SetMaxSize((largeur, hauteur))" in source
    assert "self.sizer_pages = wx.BoxSizer(wx.VERTICAL)" in source
    assert "page.Reparent(self)" in source
    assert "GetTextExtent(self.label)" in source
    assert "ActiveToolBook" in source
    assert "MAJ_page_si_affichee" in source
