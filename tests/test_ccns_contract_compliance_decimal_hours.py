from datetime import date
from decimal import Decimal

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter


def test_monthly_compliance_preserves_quarter_hour_precision() -> None:
    presenter = CCNSContractCompliancePresenter()

    preview = presenter.evaluate_monthly(
        group_code="G1",
        reference_date=date(2026, 9, 1),
        weekly_hours=Decimal("21.25"),
        remuneration_amount=Decimal("9999.99"),
    )

    assert preview.weekly_hours == Decimal("21.25")
    assert preview.weekly_hours != Decimal("21.00")
    assert preview.remuneration_amount == Decimal("9999.99")
