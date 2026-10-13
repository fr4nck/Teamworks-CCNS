import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSISTANT = ROOT / "teamworks" / "Dlg" / "DLG_Assistant_demarrage.py"
BUTTON = ROOT / "teamworks" / "Ctrl" / "CTRL_Bouton_image.py"
PUBLISHER = ROOT / "teamworks" / "Dlg" / "DLG_Publiposteur.py"
CONTRACT = ROOT / "teamworks" / "Dlg" / "DLG_Creation_contrat.py"
CONTRACT_START = ROOT / "teamworks" / "Ctrl" / "CTRL_Creation_contrat_p2.py"
PREFERENCES = ROOT / "teamworks" / "Dlg" / "DLG_Preferences.py"
GENERAL = ROOT / "teamworks" / "Ctrl" / "CTRL_Page_generalites.py"


def _definition_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item
        for item in tree.body
        if isinstance(item, (ast.ClassDef, ast.FunctionDef)) and item.name == name
    )
    return ast.get_source_segment(source, node)


def _load_function(path: Path, name: str):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(
        item
        for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace[name]


def test_startup_close_action_uses_native_text_focus_and_square_icon() -> None:
    source = ASSISTANT.read_text(encoding="utf-8")
    common_button = BUTTON.read_text(encoding="utf-8")

    assert 'texte=_(u"Fermer")' in source
    assert 'Images/32x32/Fermer.png' in source
    assert "Fermer_assistant.png" not in source
    assert 'role="primary"' in source
    assert "self.bouton_ok.SetFocus()" in source
    assert "class CTRL(wx.Button):" in common_button


def test_publisher_document_commands_wrap_below_the_list() -> None:
    page = _definition_source(PUBLISHER, "Page4")

    assert "sizer_boutons = wx.WrapSizer(wx.HORIZONTAL, 0)" in page
    assert "sizer_choix_contenu.Add(self.listCtrl, 1, wx.EXPAND" in page
    assert "sizer_choix_contenu.Add(sizer_boutons, 0, wx.EXPAND)" in page
    for name in ("importer", "actualiser", "ajouter", "modifier", "supprimer"):
        assert "self.bouton_%s," % name in page
    assert "grid_sizer_choix = wx.FlexGridSizer(rows=1, cols=2" not in page


def test_contract_start_and_characteristics_share_one_logical_step() -> None:
    dialog = CONTRACT.read_text(encoding="utf-8")
    start = CONTRACT_START.read_text(encoding="utf-8")
    navigation = _load_function(CONTRACT, "_contract_navigation_pages")

    assert navigation(False) == (1, 2, 4, 6)
    assert navigation(True) == (1, 2, 4, 5, 6)
    assert "NAVIGATION_PAGES = _contract_navigation_pages(True)" in dialog
    assert "return (self.page2, self.page3)" in dialog
    assert "for page in self._PagesForStep(self.pageVisible):" in dialog
    assert "if page.Validation() is False:" in dialog
    assert "proportion = 0 if numPage == 2 else 1" in dialog
    assert "1. Point de départ et caractéristiques du contrat" in start
    assert 'self.label_titre.SetLabel(_(u"Caractéristiques générales du contrat"))' in dialog


def test_preferences_stack_labels_and_long_report_action() -> None:
    source = PREFERENCES.read_text(encoding="utf-8")
    ligne_start = source.index("    def _ligne(parent, label, control):")
    ligne_end = source.index("\n    def OnSize", ligne_start)
    ligne = source[ligne_start:ligne_end]

    assert "wx.BoxSizer(wx.VERTICAL)" in ligne
    assert "ligne.Add(etiquette, 0, wx.EXPAND | wx.BOTTOM, gap)" in ligne
    assert "ligne.Add(control, 0, wx.EXPAND)" in ligne
    assert "adresse_rapport_bugs = wx.BoxSizer(wx.VERTICAL)" in source
    assert "self.body.FitInside()" in source


def test_individual_header_formats_all_identity_combinations() -> None:
    formatter = _load_function(GENERAL, "_formater_nom_prenom")

    assert formatter("DUPONT", "Alice") == "DUPONT, Alice"
    assert formatter("DUPONT", "") == "DUPONT"
    assert formatter("", "Alice") == "Alice"
    assert formatter("", "", "NOM, Prénom") == "NOM, Prénom"

    source = GENERAL.read_text(encoding="utf-8")
    initial_refresh = source.index("        self.SetEtatNumSecu()")
    header_refresh = source.index("        self.MaJ_NomPrenom_Fiche()", initial_refresh)
    address_refresh = source.index("        self.MaJ_Adresse_Fiche()", initial_refresh)
    assert initial_refresh < header_refresh < address_refresh
