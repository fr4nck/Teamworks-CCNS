import ast
from pathlib import Path


BANDEAU_PATH = Path("teamworks/Ctrl/CTRL_Bandeau.py")
FOOTER_PATH = Path("teamworks/Ctrl/CTRL_Footer.py")


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


def test_common_theme_controls_remain_valid_python():
    _tree(BANDEAU_PATH)
    _tree(FOOTER_PATH)
