from pathlib import Path
import ast


ROOT = Path("teamworks")
BUTTON_PATH = ROOT / "Ctrl" / "CTRL_Bouton_image.py"
FOOTER_PATH = ROOT / "Ctrl" / "CTRL_Footer.py"
TEXT_PATH = ROOT / "Ctrl" / "CTRL_Texte.py"
SECTION_PATH = ROOT / "Ctrl" / "CTRL_Section.py"
STYLES_PATH = ROOT / "Utils" / "UTILS_Styles.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _class_methods(path, class_name):
    tree = ast.parse(_source(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    raise AssertionError("Classe %s introuvable dans %s" % (class_name, path))


def test_semantic_text_components_use_central_typography_and_tokens():
    source = _source(TEXT_PATH)
    assert "UTILS_Styles.GetFont" in source
    assert "UTILS_Interface.GetToken" in source
    assert "wx.Font(" not in source


def test_section_component_uses_semantic_surface_and_text():
    source = _source(SECTION_PATH)
    assert "CTRL_Texte" in source
    assert "UTILS_Interface.GetToken" in source
    assert "wx.Font(" not in source


def test_footer_follows_real_columns_and_global_metrics():
    source = _source(FOOTER_PATH)
    assert "GetColumnWidth(index)" in source
    assert "return colonne.width" in source
    assert 'UTILS_Styles.GetFont("caption")' in source
    assert 'GetControlMetric("footer_min_height")' in source
    assert 'GetControlMetric("footer_text_padding")' in source
    assert 'GetSpacing("xs")' in source
    assert "UTILS_Customize" not in source
    assert "wx.Font(8" not in source


def test_common_image_button_keeps_native_rendering_and_semantic_text():
    source = _source(BUTTON_PATH)
    methods = _class_methods(BUTTON_PATH, "CTRL")
    assert "from Utils import UTILS_Interface, UTILS_Styles" in source
    # La couleur n'est plus figée à on_surface : elle dépend du rôle
    # sémantique du bouton (default/primary/danger/quiet).
    assert 'return "on_surface"' in source
    assert 'UTILS_Interface.GetToken(_token_texte_bouton(role))' in source
    assert 'UTILS_Styles.GetFont("label")' in source
    assert "wx.Font(9, wx.SWISS" not in source
    assert "AppliquerTheme" in methods


def test_common_image_button_consumes_global_icon_and_control_metrics():
    source = _source(BUTTON_PATH)
    assert "UTILS_Customize" not in source
    assert 'UTILS_Styles.ICON_SIZES["medium"]' in source
    assert 'UTILS_Styles.CONTROL_METRICS["button_icon_margin"]' in source
    assert 'GetControlMetric("button_min_height")' in source
    assert "_echelle_taille" in source
    assert "Image.Resampling.LANCZOS" in source
    assert "SetMinSize" in source


def test_button_roles_and_toggle_share_the_common_contract():
    source = _source(BUTTON_PATH)
    assert "BUTTON_ROLES" in source
    assert 'class Toggle(wx.ToggleButton):' in source
    assert "_appliquer_contrat_bouton" in source
    assert "SetRole" in source
