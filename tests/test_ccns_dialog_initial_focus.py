from pathlib import Path


DETAIL_DIALOG = Path("teamworks/Dlg/DLG_CCNS_salary_control_detail.py")
SUMMARY_DIALOG = Path("teamworks/Dlg/DLG_CCNS_employee_salary_summary.py")


def test_salary_control_detail_focuses_the_close_action_on_open():
    source = DETAIL_DIALOG.read_text(encoding="utf-8")
    assert "self.button_close.SetFocus()" in source


def test_employee_salary_summary_focuses_the_working_list_or_close_action():
    source = SUMMARY_DIALOG.read_text(encoding="utf-8")
    assert "self.list_ctrl.SetFocus()" in source
    assert "self.button_close.SetFocus()" in source
