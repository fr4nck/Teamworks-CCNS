from __future__ import annotations

import ast
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path


DIALOG_SOURCE = Path("teamworks/Dlg/DLG_Creation_contrat.py")


def _page3_method(name: str) -> ast.FunctionDef:
    tree = ast.parse(DIALOG_SOURCE.read_text(encoding="utf-8"))
    page3 = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Page3"
    )
    return next(
        node for node in page3.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_low_legacy_decimal_precision_can_break_salary_quantization():
    with localcontext() as context:
        context.prec = 4
        try:
            Decimal("1848.42").quantize(Decimal("0.01"))
        except InvalidOperation:
            pass
        else:
            raise AssertionError("Le scénario de régression doit reproduire InvalidOperation")


def test_contract_page_protects_salary_prefill_with_local_decimal_context():
    method = _page3_method("_MaybePrefillSalary")
    source = ast.unparse(method)
    assert "localcontext()" in source
    assert "max(28, context.prec)" in source
    assert "super()._MaybePrefillSalary(amount)" in source


def test_contract_page_also_protects_salary_reading_and_validation():
    for method_name in ("_MonthlySalaryDecimal", "Validation"):
        source = ast.unparse(_page3_method(method_name))
        assert "localcontext()" in source
        assert "max(28, context.prec)" in source
