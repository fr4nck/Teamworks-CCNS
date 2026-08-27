import ast
from pathlib import Path


SOURCE = Path("teamworks/Ctrl/CTRL_Navigation_principale.py")
MAIN = Path("teamworks/Teamworks.py")
CORE = Path("teamworks/Teamworks_core.py")
TEMP_BACKUP = Path("teamworks/Teamworks.py.bak-tw189")
TEMP_WORKFLOW = Path(".github/workflows/tw189-integrate-navigation.yml")


def _source(path=SOURCE):
    return path.read_text(encoding="utf-8")


def _dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def _called_names(path=SOURCE):
    tree = ast.parse(_source(path))
    return {
        name
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for name in [_dotted_name(node.func)]
        if name
    }


def test_navigation_source_is_valid_python():
    ast.parse(_source())


def test_navigation_replaces_fixed_toolbook_geometry():
    source = _source()
    calls = _called_names()

    assert "wx.Toolbook" not in calls
    assert "wx.Simplebook" not in calls
    assert "wx.WrapSizer(wx.HORIZONTAL)" in source
    assert "class BoutonNavigation(wx.Control)" in source
    assert "wx.ToggleButton" not in calls
    assert "self.sizer_pages = wx.BoxSizer(wx.VERTICAL)" in source


def test_navigation_pages_keep_historical_parent_depth():
    source = _source()

    assert "page.Reparent(self)" in source
    assert "self.sizer_pages.Add(page, 1, wx.EXPAND)" in source
    assert "page.Hide()" in source
    assert "self._pages[index].Show()" in source


def test_navigation_buttons_keep_full_labels_and_scale_their_targets():
    source = _source()

    assert "GetTextExtent(self.label)" in source
    assert '"echelle_interface"' in source
    assert '"echelle_police"' in source
    assert source.index('"echelle_interface"') < source.index('"echelle_police"')
    assert "ajouter_si_manquant=False" in source
    assert "wx.IMAGE_QUALITY_HIGH" in source
    assert "SetMinSize((largeur, hauteur))" in source
    assert "SetMaxSize((largeur, hauteur))" in source


def test_navigation_is_painted_with_semantic_tokens_instead_of_native_chrome():
    source = _source()

    assert "wx.AutoBufferedPaintDC" in source
    assert 'GetToken("surface_container_low")' in source
    assert 'GetToken("primary_container")' in source
    assert 'GetToken("on_primary_container")' in source
    assert "bouton.Bind(wx.EVT_BUTTON" in source


def test_navigation_uses_semantic_active_and_inactive_states():
    source = _source()

    assert 'GetToken("primary_container")' in source
    assert 'GetToken("on_primary_container")' in source
    assert 'GetToken("surface")' in source
    assert 'GetToken("on_surface")' in source


def test_navigation_preserves_teamworks_book_api():
    source = _source()
    tree = ast.parse(source)
    navigation = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "NavigationPrincipale"
    )
    methods = {
        node.name for node in navigation.body if isinstance(node, ast.FunctionDef)
    }

    assert {
        "AddPage",
        "GetPage",
        "GetPageCount",
        "GetSelection",
        "SetSelection",
        "ChangeSelection",
        "MAJ_page_si_affichee",
        "MAJ_panel",
        "ActiveToolBook",
    } <= methods


def test_navigation_wraps_instead_of_truncating_labels():
    source = _source()

    assert "wx.WrapSizer" in source
    assert "Ellips" not in source
    assert "SetToolBitmapSize" not in source


def test_main_program_uses_flexible_navigation_once_integrated():
    source = _source(MAIN)

    assert "CTRL_Navigation_principale" in source
    assert "class Toolbook(wx.Toolbook)" not in source
    assert "class Toolbook(CTRL_Navigation_principale.NavigationPrincipale)" in source
    assert "GetToolBar()" not in source.split("class Toolbook", 1)[1].split(
        "CORE.Toolbook", 1
    )[0]


def test_modern_entrypoint_keeps_historical_core_isolated():
    main = _source(MAIN)
    core = _source(CORE)

    ast.parse(main)
    ast.parse(core)
    assert "import Teamworks_core as CORE" in main
    assert "CORE.Toolbook = Toolbook" in main
    assert "MyFrame = CORE.MyFrame" in main
    assert "MyApp = CORE.MyApp" in main
    assert "CORE.CUSTOMIZE = customize" in main
    assert "class MyFrame(wx.Frame)" in core
    assert not TEMP_BACKUP.exists()
    assert not TEMP_WORKFLOW.exists()
