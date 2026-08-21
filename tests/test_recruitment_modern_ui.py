import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "teamworks" / "Ctrl" / "CTRL_Recrutement.py"
RESUME = ROOT / "teamworks" / "Ctrl" / "CTRL_Recrutement_resume.py"
NAV = ROOT / "teamworks" / "Ctrl" / "CTRL_Recrutement_navigation.py"
CORE = ROOT / "teamworks" / "Ctrl" / "CTRL_Recrutement_core.py"
GADGET = ROOT / "teamworks" / "Ctrl" / "CTRL_Gadget_candidatures.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def test_recruitment_components_are_valid_python():
    for path in (PAGE, RESUME, NAV, CORE, GADGET):
        ast.parse(_source(path))


def test_recruitment_keeps_historical_business_core_isolated():
    page = _source(PAGE)
    core = _source(CORE)
    assert "from Ctrl import CTRL_Recrutement_core as CORE" in page
    assert "from Ctrl import CTRL_Recrutement_resume as RESUME" in page
    assert "from Ctrl import CTRL_Recrutement_navigation as NAV" in page
    assert "class PanelResume" in core
    assert "class ToolBar" in core
    assert "class BarreRecherche" in core
    assert "class Panel(wx.Panel):" in core


def test_recruitment_page_removes_legacy_blue_chrome():
    source = _source(PAGE)
    for legacy in (
        "MultiSplitterWindow",
        "PanelArrondi",
        "wx.SUNKEN_BORDER",
        "wx.BitmapButton",
        "wx.FlexGridSizer",
        ".Fit(self)",
        "(122, 161, 230)",
        "(214, 223, 247)",
        "wx.Font(",
        "wx.ImageList(16, 16)",
        "panel_vide",
    ):
        assert legacy not in source
    assert "CTRL_Section.Section(" in source
    assert 'CTRL_Texte.H2(self.window_D, _(u"Candidats"))' in source
    assert "wx.WrapSizer(wx.HORIZONTAL)" in source


def test_recruitment_preserves_parent_chain_expected_by_object_list_views():
    page = _source(PAGE)
    resume = _source(RESUME)
    assert "self.splitter = wx.SplitterWindow(" in page
    assert "self.window_D = wx.Panel(self.splitter" in page
    assert "OL_candidats.ListView(\n            self.window_D" in page
    assert "OL_candidatures.ListView(\n            self.window_D" in page
    assert "OL_entretiens.ListView(\n            self.window_D" in page
    assert "OL_emplois.ListView(\n            self.window_D" in page
    assert "self.noteBook = wx.Notebook(self, -1)" in resume
    assert "list -> notebook -> PanelResume -> window_D" in resume


def test_recruitment_navigation_is_textual_and_flexible():
    source = _source(NAV)
    assert "class BoutonMode(wx.ToggleButton):" in source
    assert "class BarreModes(wx.Panel):" in source
    assert "wx.WrapSizer(wx.HORIZONTAL)" in source
    assert 'GetControlMetric("button_min_height")' in source
    assert "Images/16x16" not in source
    assert "wx.StaticBitmap" not in source
    assert "wx.RED" not in source
    assert "wx.BLACK" not in source


def test_recruitment_detail_uses_semantic_typography():
    source = _source(RESUME)
    assert "CTRL_Texte.H2" in source
    assert "CTRL_Texte.H3" in source
    assert "CTRL_Texte.BodySecondary" in source
    assert "wx.Font(" not in source
    assert "wx.ImageList" not in source
    assert "size=(-1, 150)" not in source


def test_recruitment_tracking_gadget_uses_charter():
    source = _source(GADGET)
    assert "Tekton" not in source
    assert "SetPointSize" not in source
    assert "wx.FFont" not in source
    assert ".Fit(self)" not in source
    assert 'UTILS_Styles.GetFont("body-small")' in source
    assert 'UTILS_Interface.GetToken("primary_container")' in source


def test_recruitment_actions_and_workspace_remain_available():
    page = _source(PAGE)
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
        assert '_(u"%s")' % label in page
    assert "self.section_entretiens" in page
    assert "self.section_informations" in page
    assert "SetSashGravity(0.22)" in page
    assert "UTILS_Styles.Scale(330)" in page
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in page


def test_recruitment_business_contract_remains_available():
    page = _source(PAGE)
    for contract in (
        "def OnBoutonAjouter",
        "def OnBoutonModifier",
        "def OnBoutonSupprimer",
        "def OnBoutonCourrier",
        "def OnBoutonImprimer",
        "def OnBoutonExportTexte",
        "def OnBoutonExportExcel",
        "def MAJapresVerrouillage",
    ):
        assert contract in page
