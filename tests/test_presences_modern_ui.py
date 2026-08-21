import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "teamworks" / "Ctrl" / "CTRL_Presences.py"
CALENDAR = ROOT / "teamworks" / "Ctrl" / "CTRL_Presences_calendrier.py"
LEGEND = ROOT / "teamworks" / "Ctrl" / "CTRL_Presences_legende.py"
PEOPLE = ROOT / "teamworks" / "Ctrl" / "CTRL_Presences_personnes.py"
COMMON = ROOT / "teamworks" / "Ctrl" / "CTRL_Presences_common.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_presence_components_are_valid_python():
    for path in (MAIN, CALENDAR, LEGEND, PEOPLE, COMMON):
        ast.parse(_source(path))


def test_presence_shell_uses_semantic_sections_and_responsive_splitter():
    source = _source(MAIN)
    assert "MultiSplitterWindow" not in source
    assert "FonctionsPerso.PanelArrondi" not in source
    assert ".Fit(self)" not in source
    assert "CTRL_Section.Section(" in source
    assert source.count("CTRL_Section.Section(") == 3
    assert 'titre=_(u"Calendrier")' in source
    assert 'titre=_(u"Légende")' in source
    assert 'titre=_(u"Individus")' in source
    assert "SetSashGravity(0.24)" in source
    assert 'UTILS_Styles.Scale(330)' in source


def test_presence_calendar_has_no_hand_painted_legacy_chrome():
    source = _source(CALENDAR)
    assert "GradientFillLinear" not in source
    assert "DrawRoundedRectangle" not in source
    assert "wx.Font(" not in source
    assert "couleurFondPanneau" not in source
    assert "couleurFondWidgets" not in source
    assert 'UTILS_Interface.GetToken("primary")' in source
    assert 'UTILS_Interface.GetToken("warning")' in source
    assert "def MAJselectionDates" in source
    assert "find_presences_panel" in source


def test_presence_legend_removes_demo_popup_and_legacy_blue():
    source = _source(LEGEND)
    assert "Bonjour !" not in source
    assert "Ca va ?" not in source
    assert "Ajouter1" not in source
    assert "IDLE" not in source
    assert "ggamer@wanadoo.fr" not in source
    assert "#EEF4FB" not in source
    assert "wx.Font(" not in source
    assert "AjusterColonnes" in source
    assert 'UTILS_Styles.GetIconSize("small")' in source


def test_presence_people_use_one_checkbox_implementation_on_phoenix():
    source = _source(PEOPLE)
    assert '_CheckboxFallback = object if _PHOENIX else CheckListCtrlMixin' in source
    assert 'if _PHOENIX:\n            self.EnableCheckBoxes(True)\n        else:\n            CheckListCtrlMixin.__init__(self)' in source
    assert "IsItemChecked" in source
    assert "EVT_LIST_ITEM_CHECKED" in source
    assert "EVT_LIST_ITEM_UNCHECKED" in source
    assert "wx.RED" not in source
    assert "wx.BLACK" not in source
    assert 'token = "primary" if key in liste_presents else "on_surface"' in source


def test_presence_people_keep_business_actions():
    source = _source(PEOPLE)
    for method in (
        "Menu_40",
        "Menu_50",
        "Menu_55",
        "Menu_60",
        "Menu_70",
        "Menu_80",
        "Menu_90",
        "Import_Personnes",
    ):
        assert "def %s" % method in source
    assert "DLG_Application_modele.Dialog" in source
    assert "CTRL_Page_presences.Dialog" in source
    assert "DLG_Impression_calendrier_annuel.MyDialog" in source
