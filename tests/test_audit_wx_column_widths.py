from pathlib import Path

from scripts.audit_runtime_risks import audit_ast


def _audit(source: str):
    root = Path(".").resolve()
    path = root / "teamworks" / "dummy.py"
    return audit_ast(root, path, source.splitlines())


def test_detects_true_division_in_set_column_width():
    findings = _audit("ctrl.SetColumnWidth(0, self.GetSize()[0] / 2)")
    assert any(item.category == "wx-column-width-float-risk" for item in findings)


def test_detects_float_literal_in_set_column_width():
    findings = _audit("ctrl.SetColumnWidth(0, largeur * 0.5)")
    assert any(item.category == "wx-column-width-float-risk" for item in findings)


def test_accepts_integer_width_expression():
    findings = _audit("ctrl.SetColumnWidth(0, int(self.GetSize()[0] / 2))")
    assert not any(item.category == "wx-column-width-float-risk" for item in findings)


def test_accepts_integer_literal():
    findings = _audit("ctrl.SetColumnWidth(0, 120)")
    assert not any(item.category == "wx-column-width-float-risk" for item in findings)
