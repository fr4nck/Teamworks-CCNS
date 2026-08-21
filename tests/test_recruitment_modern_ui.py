import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "teamworks" / "Ctrl" / "CTRL_Recrutement.py"
CORE = ROOT / "teamworks" / "Ctrl" / "CTRL_Recrutement_core.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_recruitment_shell_and_core_are_valid_python():
    ast.parse(_source(SHELL))
    ast.parse(_source(CORE))


def test_recruitment_keeps_historical_business_core_isolated():
    shell = _source(SHELL)
    core = _source(CORE)
    assert "from Ctrl import CTRL_Recrutement_core as CORE" in shell
    assert "class Panelidentite(CORE.Panelidentite):" in shell
    assert "class Panel(wx.Panel):" in shell
    assert "class PanelResume" in core
    assert "class ToolBar" in core
    assert "class BarreRecherche" in core
    assert "class Panel(wx.Panel):" in core


def test_recruitment_shell_removes_legacy_blue_chrome():
    shell = _source(SHELL)
    assert "MultiSplitterWindow" not in shell
    assert "PanelArrondi" not in shell
    assert "wx.SUNKEN_BORDER" not in shell
    assert "wx.BitmapButton" not in shell
    assert "wx.FlexGridSizer" not in shell
    assert ".Fit(self)" not in shell
    assert "(122, 161, 230)" not in shell
    assert "(214, 223, 247)" not in shell
    assert "wx.Font(" not in shell
    assert "wx.ImageList(16, 16)" not in shell


def test_recruitment_uses_semantic_navigation_sections_and_actions():
    shell = _source(SHELL)
    assert 'CTRL_Texte.H2(self.window_D, _(u"Candidats"))' in shell
    assert shell.count("CTRL_Section.Section(") >= 3
    assert "class BoutonMode(wx.ToggleButton):" in shell
    assert "class ToolBar(wx.Panel):" in shell
    for label in (
        "Ajouter",
        "Modifier",
        "Supprimer",
        "Filtres",
        "Tout afficher",
        "Colonnes",
        "Courrier",
        "Imprimer",
        "Export texte",
        "Export Excel",
        "Aide",
    ):
        assert 'texte=_(u"%s")' % label in shell
    assert "wx.WrapSizer(wx.HORIZONTAL)" in shell


def test_recruitment_preserves_parent_chain_expected_by_object_list_views():
    shell = _source(SHELL)
    assert "self.splitter = wx.SplitterWindow(" in shell
    assert "self.window_D = wx.Panel(self.splitter" in shell
    assert "OL_candidats.ListView(\n            self.window_D" in shell
    assert "OL_candidatures.ListView(\n            self.window_D" in shell
    assert "OL_entretiens.ListView(\n            self.window_D" in shell
    assert "OL_emplois.ListView(\n            self.window_D" in shell


def test_recruitment_uses_flexible_workspace_instead_of_dead_blue_column():
    shell = _source(SHELL)
    assert "self.section_entretiens" in shell
    assert "self.section_informations" in shell
    assert "panel_vide" not in shell
    assert "SetSashGravity(0.22)" in shell
    assert "UTILS_Styles.Scale(330)" in shell
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in shell
