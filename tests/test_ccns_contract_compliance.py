from datetime import date
from decimal import Decimal, localcontext

import pytest

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity


def test_group_choices_expose_ccns_2026_groups_and_periodicity():
    presenter = CCNSContractCompliancePresenter()

    choices = presenter.group_choices(date(2026, 8, 19))

    assert [choice.code for choice in choices] == [f"G{number}" for number in range(1, 9)]
    assert all(choice.periodicity is SalaryMinimumPeriodicity.MONTHLY for choice in choices[:6])
    assert all(choice.periodicity is SalaryMinimumPeriodicity.ANNUAL for choice in choices[6:])
    assert choices[0].minimum_amount == Decimal("1848.42")
    assert choices[5].minimum_amount == Decimal("2865.97")


def test_grid_and_salary_control_are_independent_from_ambient_decimal_precision():
    # Le runtime historique peut laisser une précision Decimal très faible.
    # Construction de grille et calcul du minimum doivent rester déterministes,
    # sans modifier cette précision globale pour le reste de Teamworks.
    with localcontext() as context:
        context.prec = 5
        presenter = CCNSContractCompliancePresenter()
        assert context.prec == 5
        choices = presenter.group_choices(date(2026, 8, 19))
        preview = presenter.evaluate_monthly(
            group_code="G1",
            reference_date=date(2026, 8, 19),
            weekly_hours=Decimal("35.00"),
            remuneration_amount=Decimal("1900.00"),
        )
        assert context.prec == 5

    assert choices[6].minimum_amount == Decimal("40597.94")
    assert choices[7].minimum_amount == Decimal("46833.81")
    assert preview.ccns_minimum_amount == Decimal("1848.42")
    assert preview.smic_minimum_amount == Decimal("1867.02")
    assert preview.required_minimum_amount == Decimal("1867.02")
    assert preview.difference_amount == Decimal("32.98")
    assert preview.compliant is True


def test_monthly_preview_uses_more_favourable_ccns_or_smic_minimum():
    presenter = CCNSContractCompliancePresenter()

    preview = presenter.evaluate_monthly(
        group_code="G1",
        reference_date=date(2026, 8, 19),
        weekly_hours=Decimal("35.00"),
        remuneration_amount=Decimal("1900.00"),
    )

    assert preview.ccns_minimum_amount == Decimal("1848.42")
    assert preview.smic_minimum_amount == Decimal("1867.02")
    assert preview.required_minimum_amount == Decimal("1867.02")
    assert preview.source == "smic"
    assert preview.compliant is True
    assert preview.difference_amount == Decimal("32.98")


def test_g7_g8_are_not_silently_converted_to_monthly_minimum():
    presenter = CCNSContractCompliancePresenter()

    with pytest.raises(ValueError, match="minimum annuel"):
        presenter.evaluate_monthly(
            group_code="G7",
            reference_date=date(2026, 8, 19),
            weekly_hours=Decimal("35.00"),
            remuneration_amount=Decimal("3500.00"),
        )
