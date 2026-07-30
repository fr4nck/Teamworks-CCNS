from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "Dlg" / "DLG_Selection_liste.py"


def test_selection_list_uses_one_native_checkbox_api():
    source = TARGET.read_text(encoding="utf-8")

    assert "CheckListCtrlMixin" not in source
    assert "self.EnableCheckBoxes(True)" in source
    assert "self.IsItemChecked(index)" in source
    assert "self.IsChecked(index)" not in source


def test_double_click_toggles_the_native_checkbox():
    source = TARGET.read_text(encoding="utf-8")

    assert "self.CheckItem(evt.Index, not self.IsItemChecked(evt.Index))" in source
