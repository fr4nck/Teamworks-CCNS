import ast
from pathlib import Path


ROOT = Path("teamworks")
CUSTOMIZE = ROOT / "Utils" / "UTILS_Customize.py"
PERSONS = ROOT / "Ctrl" / "CTRL_Personnes.py"
CONTRACTS = ROOT / "Ctrl" / "CTRL_Page_contrats.py"
PERSON_DIALOG = ROOT / "Dlg" / "DLG_Fiche_individuelle.py"
BUTTON = ROOT / "Ctrl" / "CTRL_Bouton_image.py"
GADGET = ROOT / "Gadget.py"
RESPONSIVE = ROOT / "Utils" / "UTILS_Responsive.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_refactored_sources_are_valid_python():
    for path in (CUSTOMIZE, PERSONS, CONTRACTS, PERSON_DIALOG, BUTTON, GADGET):
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


def test_components_read_interface_scale_before_legacy_font_scale():
    for path in (PERSONS, CONTRACTS, BUTTON, GADGET):
        source = _source(path)
        assert '"echelle_interface"' in source
        assert '"echelle_police"' in source
        assert source.index('"echelle_interface"') < source.index('"echelle_police"')
        assert "ajouter_si_manquant=False" in source


def test_icons_scale_in_their_own_components_not_with_a_global_patch():
    persons = _source(PERSONS)
    contracts = _source(CONTRACTS)
    dialog = _source(PERSON_DIALOG)
    button = _source(BUTTON)

    assert "wx.IMAGE_QUALITY_HIGH" in persons
    assert "wx.IMAGE_QUALITY_HIGH" in contracts
    assert "wx.IMAGE_QUALITY_HIGH" in dialog
    assert "_echelle_valeur(36, 36)" in button


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
