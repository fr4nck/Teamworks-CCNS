import ast
from pathlib import Path


SOURCE = Path("teamworks/Ctrl/CTRL_Navigation_principale.py")


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_navigation_source_is_valid_python():
    ast.parse(_source())


def test_navigation_replaces_fixed_toolbook_geometry():
    source = _source()

    assert "wx.Toolbook" not in source
    assert "wx.Simplebook" in source
    assert "wx.WrapSizer(wx.HORIZONTAL)" in source
    assert "wx.ToggleButton" in source


def test_navigation_buttons_keep_full_labels_and_scale_their_targets():
    source = _source()

    assert "GetBestSize()" in source
    assert '"echelle_interface"' in source
    assert '"echelle_police"' in source
    assert source.index('"echelle_interface"') < source.index('"echelle_police"')
    assert "ajouter_si_manquant=False" in source
    assert "wx.IMAGE_QUALITY_HIGH" in source
    assert "SetMinSize((largeur, hauteur))" in source


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
    assert "SetLabel(" not in source
    assert "Ellips" not in source
    assert "SetToolBitmapSize" not in source
