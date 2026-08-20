import ast
from pathlib import Path


BANDEAU_PATH = Path("teamworks/Ctrl/CTRL_Bandeau.py")
FOOTER_PATH = Path("teamworks/Ctrl/CTRL_Footer.py")
BUTTON_PATH = Path("teamworks/Ctrl/CTRL_Bouton_image.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def _tree(path):
    return ast.parse(_source(path))


def _class_methods(path, class_name):
    tree = _tree(path)
    cls = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return {
        node.name
        for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_bandeau_uses_semantic_theme_tokens():
    source = _source(BANDEAU_PATH)

    assert "from Utils import UTILS_Interface" in source
    assert 'GetToken("surface_container_high")' in source
    assert 'GetToken("on_surface")' in source
    assert 'GetToken("on_surface_variant")' in source
    assert 'GetToken("outline_variant")' in source
    assert "wx.Colour(255, 255, 255)" not in source


def test_bandeau_keeps_explicit_theme_refresh_api():
    assert "AppliquerTheme" in _class_methods(BANDEAU_PATH, "Bandeau")
    assert "SetTexte" in _class_methods(BANDEAU_PATH, "MyHtml")


def test_bandeau_no_longer_uses_fixed_grid_or_fit_geometry():
    source = _source(BANDEAU_PATH)

    assert "FlexGridSizer" not in source
    assert ".Fit(self)" not in source
    assert "wx.BoxSizer" in source
    assert "SYS_DEFAULT_GUI_FONT" in source
    assert '"echelle_police"' in source
    assert "SetMinSize((-1, _echelle_valeur(hauteur, 25)))" in source


def test_footer_uses_semantic_theme_tokens():
    source = _source(FOOTER_PATH)

    assert "from Utils import UTILS_Interface" in source
    assert 'GetToken("surface_container_high")' in source
    assert 'GetToken("on_surface_variant"' in source
    assert "wx.Colour(140, 140, 140)" in source  # fallback only


def test_footer_keeps_explicit_theme_refresh_api():
    methods = _class_methods(FOOTER_PATH, "Footer")

    assert "AppliquerTheme" in methods
    assert "OnPaint" in methods


def test_common_image_button_keeps_native_rendering_and_semantic_text():
    source = _source(BUTTON_PATH)
    methods = _class_methods(BUTTON_PATH, "CTRL")

    assert "from Utils import UTILS_Interface" in source
    assert 'GetToken("on_surface")' in source
    assert "SYS_DEFAULT_GUI_FONT" in source
    assert "wx.Font(9, wx.SWISS" not in source
    assert "AppliquerTheme" in methods


def test_common_image_button_scales_image_and_action_target_directly():
    source = _source(BUTTON_PATH)

    assert "from Utils import UTILS_Customize" in source
    assert '"echelle_police"' in source
    assert "_echelle_taille" in source
    assert "Image.Resampling.LANCZOS" in source
    assert "hauteur_min = _echelle_valeur(32, 32)" in source
    assert "SetMinSize" in source


def test_common_image_button_no_longer_contains_runtime_migration_scripts():
    source = _source(BUTTON_PATH)

    assert "def ModifieFichiers" not in source
    assert "class Dialog(wx.Dialog)" not in source
    assert "os.listdir(os.getcwd())" not in source


def test_common_theme_controls_remain_valid_python():
    _tree(BANDEAU_PATH)
    _tree(FOOTER_PATH)
    _tree(BUTTON_PATH)
