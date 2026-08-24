import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Ctrl" / "CTRL_Calendrier_tw.py"
CORE = ROOT / "teamworks" / "Ctrl" / "CTRL_Calendrier_tw_core.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_calendar_shell_and_core_are_valid_python():
    ast.parse(_source(SHELL))
    ast.parse(_source(CORE))


def test_calendar_shell_keeps_historical_engine_explicitly_isolated():
    shell = _source(SHELL)
    core = _source(CORE)
    assert "from Ctrl import CTRL_Calendrier_tw_core as CORE" in shell
    assert "Calendrier = CORE.Calendrier" in shell
    assert "class Calendrier(wx.ScrolledWindow)" in core
    assert "def Importation_Vacances" in core
    assert "def Importation_Feries" in core
    assert "def Importation_JoursAvecPresents" in core
    assert "def SendDates" in core


def test_calendar_shell_uses_charter_instead_of_fixed_legacy_chrome():
    source = _source(SHELL)
    assert "wx.BitmapButton" not in source
    assert "wx.FlexGridSizer" not in source
    assert "Images/16x16/Calendrier_jour.png" not in source
    assert "size=(28, 21)" not in source
    assert "(70, -1)" not in source
    assert "(25, 20)" not in source
    assert "SetSize((910, 520))" not in source
    assert "SetSashPosition(450" not in source
    assert "CTRL_Bouton_image.CTRL" in source
    assert "wx.WrapSizer" in source
    assert "UTILS_Styles.GetControlMetric" in source
    assert "UTILS_Styles.GetLayoutSpacing" in source


def test_calendar_shell_palette_stays_inside_semantic_families():
    source = _source(SHELL)
    for token in (
        "surface_container_lowest",
        "surface_container_low",
        "primary_container",
        "primary",
        "warning",
        "surface_container_high",
        "on_surface",
    ):
        assert '"%s"' % token in source
    assert "wx.Colour(" not in source
    assert "(255, 162, 0)" not in source
    assert "(255, 255, 187)" not in source


def test_calendar_selection_contract_is_generic_and_callback_friendly():
    source = _source(SHELL)
    assert "def SetSelectionDates" in source
    assert "def GetSelectionDates" in source
    assert "def MAJselectionDates" in source
    assert "callbacksenddates=callbacksenddates" in source
    assert "GetGrandParent().GetParent().MAJpanelPlanning" not in source
    assert "SetTexte(_(u\"Vue mensuelle\"))" in source
    assert "SetTexte(_(u\"Vue annuelle\"))" in source
