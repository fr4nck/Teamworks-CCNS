import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIALOG = ROOT / "teamworks" / "Dlg" / "DLG_Selection_periode.py"


def _src():
    return DIALOG.read_text(encoding="utf-8")


def test_period_selection_is_valid_python():
    ast.parse(_src())


def test_period_selection_uses_semantic_sections_and_profile():
    source = _src()
    assert source.count("CTRL_Section.Section(") == 3
    for title in ("Périodes de vacances", "Mois et année", "Dates"):
        assert title in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source


def test_period_selection_has_no_legacy_layout_or_zebra():
    source = _src()
    for legacy in ("wx.StaticBox", "wx.FlexGridSizer", ".Fit(self)", "#EEF4FB", "ListCtrlAutoWidthMixin", "ColumnSorterMixin"):
        assert legacy not in source


def test_period_selection_keeps_public_contract_and_validates_order():
    source = _src()
    for method in ("GetDates", "SetDates", "GetPersonnesPresentes", "On_maj_mois", "On_maj_annee"):
        assert "def %s" % method in source
    assert "if index <= 0:" in source
    assert "if fin < debut:" in source
    assert "FROM periodes_vacances" in source
    assert "FROM presences" in source
