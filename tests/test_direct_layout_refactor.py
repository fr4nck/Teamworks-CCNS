import ast
from pathlib import Path


ROOT = Path("teamworks")
CUSTOMIZE = ROOT / "Utils" / "UTILS_Customize.py"
PERSONS = ROOT / "Ctrl" / "CTRL_Personnes.py"
CONTRACTS = ROOT / "Ctrl" / "CTRL_Page_contrats.py"
PERSON_DIALOG = ROOT / "Dlg" / "DLG_Fiche_individuelle.py"
RESPONSIVE = ROOT / "Utils" / "UTILS_Responsive.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_refactored_sources_are_valid_python():
    for path in (CUSTOMIZE, PERSONS, CONTRACTS, PERSON_DIALOG):
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


def test_icons_scale_in_their_own_components_not_with_a_global_patch():
    persons = _source(PERSONS)
    contracts = _source(CONTRACTS)
    dialog = _source(PERSON_DIALOG)

    assert "wx.IMAGE_QUALITY_HIGH" in persons
    assert "wx.IMAGE_QUALITY_HIGH" in contracts
    assert "wx.IMAGE_QUALITY_HIGH" in dialog
    assert '"echelle_police"' in persons
    assert '"echelle_police"' in contracts
    assert '"echelle_police"' in dialog
