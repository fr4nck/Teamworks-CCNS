import ast
from pathlib import Path


HELPER = Path("teamworks/Utils/UTILS_Colonnes.py")
CANDIDATURES = Path("teamworks/Ctrl/CTRL_Page_candidatures.py")


def _source(path):
    return path.read_text(encoding="utf-8")


def test_flexible_columns_helper_is_valid_python():
    ast.parse(_source(HELPER))


def test_flexible_columns_keep_historical_widths_as_minima():
    source = _source(HELPER)

    assert "largeur_disponible > total_minimum" in source
    assert "surplus = largeur_disponible - total_minimum" in source
    assert "self.listctrl.SetColumnWidth" in source
    assert "interface_scale_percent()" in source
    assert "wx.EVT_SIZE" in source


def test_flexible_columns_never_shrink_below_scaled_reference():
    source = _source(HELPER)

    assert "cibles = list(minima)" in source
    assert "if largeur_disponible > total_minimum" in source
    assert "else:" not in source.split("if largeur_disponible > total_minimum", 1)[1].split(
        "self._ajustement_en_cours = True", 1
    )[0]


def test_candidatures_choose_their_business_columns_explicitly():
    source = _source(CANDIDATURES)

    assert "UTILS_Colonnes.ColonnesFlexibles" in source
    assert "extensibles=(2, 3, 4, 5, 7)" in source
    assert "extensibles=(3, 4)" in source
    assert "wx.WrapSizer" in source
