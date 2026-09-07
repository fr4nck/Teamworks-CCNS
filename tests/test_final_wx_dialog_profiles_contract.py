from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_salary_control_detail_uses_standard_profile_without_raw_window_size():
    source = _read("teamworks/Dlg/DLG_CCNS_salary_control_detail.py")
    assert 'UTILS_Styles.ApplyWindowProfile(self, "standard")' in source
    assert "self.SetSize((760, 620))" not in source


def test_employee_salary_summary_uses_wide_profile_without_raw_window_size():
    source = _read("teamworks/Dlg/DLG_CCNS_employee_salary_summary.py")
    assert 'UTILS_Styles.ApplyWindowProfile(self, "wide")' in source
    assert "self.SetSize((1100, 650))" not in source
    assert "sizer.Add(self.list_ctrl, 1," in source


def test_startup_assistant_is_content_driven():
    source = _read("teamworks/Dlg/DLG_Assistant_demarrage.py")
    assert 'size=(730, -1)' not in source
    assert 'UTILS_Styles.ApplyWindowProfile(self, "fit")' in source
    assert "grid_sizer_base.Fit(self)" not in source
