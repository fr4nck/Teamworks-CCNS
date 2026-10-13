import ast
from pathlib import Path

ROOT = Path("teamworks")

def source(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_semantic_heights_without_limiting_stored_rows():
    tree = ast.parse(source("Utils/UTILS_Styles.py"))
    assign = next(
        n for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "FORM_VISIBLE_ROWS"
                for t in n.targets)
    )
    func = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "GetFormContentHeight"
    )
    ns = {
        "Scale": lambda value: value,
        "GetSpacing": lambda role: 4,
        "GetControlMetric": lambda role: 32,
        "GetIconSize": lambda role: (20, 20),
    }
    exec(compile(ast.Module(body=[assign, func], type_ignores=[]),
                 "<form-metrics>", "exec"), ns)
    class Control:
        def GetCharHeight(self):
            return 16
    height = ns["GetFormContentHeight"]
    assert 32 <= height(Control(), "address") < 72
    assert 32 <= height(Control(), "memo") < 130
    assert 100 <= height(Control(), "coordinates") < 150
    assert ns["FORM_VISIBLE_ROWS"]["coordinates"] == 5

def test_compact_sections_only_for_generalites():
    legacy = source("Ctrl/CTRL_Page_generalites.py")
    section = source("Ctrl/CTRL_Section.py")
    assert legacy.count('padding_role="field_gap"') == 5
    assert 'padding_role="content_padding"' in section
    for role in ("address", "coordinates", "memo"):
        assert f'GetFormContentHeight(self.' in legacy
        assert f'"{role}"' in legacy

def test_responsive_recomputes_without_old_minimum():
    adapter = source("Ctrl/CTRL_Page_generalites_091e.py")
    block = adapter.split("def _stabiliser_minimum_sections", 1)[1]
    block = block.split("def _rafraichir_taille_virtuelle", 1)[0]
    assert "contenu.SetMinSize((-1, -1))" in block
    assert "section.SetMinSize((-1, -1))" in block
    assert "contenu.GetMinSize().GetHeight()" not in block
    assert "section.GetMinSize().GetHeight()" not in block
    assert "contenu.SetMinSize((-1, hauteur_contenu))" in block
    assert "section.SetMinSize((-1, hauteur_section))" in block

def test_responsive_preserves_scroll_and_section_order():
    adapter = source("Ctrl/CTRL_Page_generalites_091e.py")
    assert "wx.ScrolledWindow" in adapter
    assert "self._scroll_host.FitInside()" in adapter
    assert "sizer.AddSpacer(section_gap)" in adapter
    assert "self._scroll_host.SetVirtualSize" in adapter
    assert "self._detacher_sections_du_layout_courant()" in adapter
