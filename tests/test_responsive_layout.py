import ast
from pathlib import Path


RESPONSIVE = Path("teamworks/Utils/UTILS_Responsive.py")
CUSTOMIZE = Path("teamworks/Utils/UTILS_Customize.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def test_responsive_module_is_valid_python():
    ast.parse(_source(RESPONSIVE))


def test_responsive_engine_is_installed_after_theme_engine():
    source = _source(CUSTOMIZE)

    assert "from Utils import UTILS_Responsive" in source
    assert "UTILS_Theme.install_auto_theming()" in source
    assert "UTILS_Responsive.install_auto_layout()" in source
    assert source.index("UTILS_Theme.install_auto_theming()") < source.index(
        "UTILS_Responsive.install_auto_layout()"
    )


def test_bitmap_actions_scale_with_font_preferences():
    source = _source(RESPONSIVE)

    assert "_adapt_bitmap_button" in source
    assert "font_scale_percent" in source
    assert "wx.IMAGE_QUALITY_HIGH" in source
    assert "SetMinSize((side, side))" in source


def test_lists_consume_free_width_without_forced_compression():
    source = _source(RESPONSIVE)

    assert "_fit_list_columns" in source
    assert "_teamworks_column_baseline" in source
    assert "if available > total:" in source
    assert "SetColumnWidth" in source
    assert "scroll horizontal" in source


def test_persons_screen_removes_useless_filler_and_keeps_sidebar_bounded():
    source = _source(RESPONSIVE)

    assert "_detach_useless_persons_filler" in source
    assert 'getattr(panel, "panel_vide", None)' in source
    assert "DetachWindow" in source
    assert "SetSashGravity(0.0)" in source
    assert "int(width * 0.28)" in source
    assert 'GetToken("surface_container_lowest")' in source


def test_person_dialog_uses_available_display_area():
    source = _source(RESPONSIVE)

    assert "_adapt_person_dialog" in source
    assert "wx.Display.GetFromWindow" in source
    assert "area.GetWidth() * 0.72" in source
    assert "area.GetHeight() * 0.78" in source


def test_contract_page_gets_adaptive_buttons_and_columns():
    source = _source(RESPONSIVE)

    assert 'name == "page_contrats"' in source
    assert '"bouton_contrats_ajouter"' in source
    assert 'getattr(panel, "list_ctrl_contrats", None)' in source
