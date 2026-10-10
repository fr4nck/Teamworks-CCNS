"""Geometry remains readable even when native text exceeds the nominal font size."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("text_height", [9, 14, 19, 28])
@pytest.mark.parametrize("cell_width", [22, 44, 70])
def test_weekday_labels_do_not_touch_day_cells(text_height, cell_width):
    source = ROOT / "teamworks/Ctrl/CTRL_Calendrier_tw_core.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
               and node.name == "Calendrier")
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                  and node.name == "DrawHeaderJours")
    wx = SimpleNamespace(Font=lambda *args: None, FONTFAMILY_DEFAULT=0,
                         FONTSTYLE_NORMAL=0, FONTWEIGHT_NORMAL=0)
    namespace = {"wx": wx}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), "exec"), namespace)
    drawn = []
    dc = SimpleNamespace(SetTextForeground=lambda *args: None,
                         SetFont=lambda *args: None,
                         DrawText=lambda text, x, y: drawn.append((text, x, y)))
    calendar = SimpleNamespace(couleurFontJours=None, ecartCases=2,
                               tailleFont=lambda *args: 7,
                               GetTextExtent=lambda text: (len(text) * 5, text_height),
                               listeCasesJours=[])
    remaining, day_top = namespace["DrawHeaderJours"](
        calendar, dc, 6, 8, 2026, 0, 0, cell_width * 7, 220)
    assert len(drawn) == 7
    assert day_top + remaining == 220
    for _, _, y in drawn:
        assert y >= 0
        assert y + text_height + 2 <= day_top
    for stored, actual in zip(calendar.listeCasesJours, drawn):
        assert stored[1] == actual[2]
        assert stored[1] + stored[3] + 2 <= day_top
