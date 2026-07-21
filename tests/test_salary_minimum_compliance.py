from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.convention import (
    CCNSClassification,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumComplianceResult,
    SalaryMinimumComplianceService,
    SalaryMinimumComplianceStatus,
    SalaryMinimumPeriodicity,
)


def group(number: int) -> CCNSClassification:
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def grid_version(code: str, start: date, end: date | None = None, amount: str = "2000.00") -> SalaryGridVersion:
    return SalaryGridVersion(
        code,
        code,
        start,
        (
            SalaryGridEntry(group(1), Decimal(amount), SalaryMinimumPeriodicity.MONTHLY),
            SalaryGridEntry(group(7), Decimal("42000.00"), SalaryMinimumPeriodicity.ANNUAL),
        ),
        effective_until=end,
    )


def service(*versions: SalaryGridVersion) -> SalaryMinimumComplianceService:
    return SalaryMinimumComplianceService(SalaryGridCatalog(versions))


def evaluate_monthly(svc: SalaryMinimumComplianceService, amount: str, hours: str, ref: date = date(2026, 1, 1)):
    return svc.evaluate(group(1), ref, Decimal(amount), SalaryMinimumPeriodicity.MONTHLY, Decimal(hours))


def test_service_selects_temporal_grid_boundaries_and_successive_versions():
    first = grid_version("A", date(2026, 1, 1), date(2026, 6, 30), "2000.00")
    second = grid_version("B", date(2026, 7, 1), amount="2100.00")
    svc = service(first, second)

    assert evaluate_monthly(svc, "2000.00", "35.00", date(2026, 1, 1)).salary_grid_version is first
    assert evaluate_monthly(svc, "2000.00", "35.00", date(2026, 6, 30)).salary_grid_version is first
    assert evaluate_monthly(svc, "2100.00", "35.00", date(2026, 7, 1)).salary_grid_version is second


def test_service_propagates_missing_grid_and_missing_group_errors():
    svc = service(grid_version("A", date(2026, 1, 1), date(2026, 1, 31)))
    with pytest.raises(ValueError, match="Aucune grille"):
        evaluate_monthly(svc, "2000.00", "35.00", date(2026, 2, 1))

    version = SalaryGridVersion("B", "B", date(2026, 1, 1), (SalaryGridEntry(group(2), Decimal("1.00"), SalaryMinimumPeriodicity.MONTHLY),))
    with pytest.raises(ValueError, match="groupe demandé"):
        service(version).evaluate(group(1), date(2026, 1, 1), Decimal("1.00"), SalaryMinimumPeriodicity.MONTHLY, Decimal("35.00"))


def test_monthly_full_time_compliance_statuses_and_no_increase_above_35h():
    svc = service(grid_version("A", date(2026, 1, 1)))
    above = evaluate_monthly(svc, "2100.00", "35.00")
    equal = evaluate_monthly(svc, "2000.00", "35.00")
    below = evaluate_monthly(svc, "1999.99", "39.00")

    assert above.status is SalaryMinimumComplianceStatus.COMPLIANT and above.difference_amount == Decimal("100.00")
    assert equal.is_exactly_at_minimum() and equal.is_compliant()
    assert below.is_non_compliant() and below.required_minimum_amount == Decimal("2000.00")
    assert below.part_time_increase_rate == Decimal("0.00")


@pytest.mark.parametrize(
    ("hours", "rate", "required"),
    [
        ("34.00", "0.00", "1942.86"),
        ("24.00", "0.00", "1371.43"),
        ("24.01", "0.00", "1372.00"),
        ("23.99", "0.02", "1398.27"),
        ("10.01", "0.02", "583.44"),
        ("10.00", "0.05", "600.00"),
        ("9.99", "0.05", "599.40"),
        ("33.333", "0.00", "1904.74"),
    ],
)
def test_monthly_part_time_proration_increase_and_round_half_up(hours, rate, required):
    result = evaluate_monthly(service(grid_version("A", date(2026, 1, 1))), "3000.00", hours)
    assert result.required_minimum_amount == Decimal(required)
    assert result.part_time_increase_rate == Decimal(rate)
    assert result.uses_part_time_increase() is (Decimal(rate) > 0)


def test_annual_groups_are_checked_without_proration_or_part_time_increase():
    svc = service(grid_version("A", date(2026, 1, 1)))
    compliant = svc.evaluate(group(7), date(2026, 1, 1), Decimal("43000.00"), SalaryMinimumPeriodicity.ANNUAL, Decimal("10.00"))
    equal = svc.evaluate(group(7), date(2026, 1, 1), Decimal("42000.00"), SalaryMinimumPeriodicity.ANNUAL, Decimal("1.00"))
    low = svc.evaluate(group(7), date(2026, 1, 1), Decimal("41999.99"), SalaryMinimumPeriodicity.ANNUAL, Decimal("23.00"))

    assert compliant.required_minimum_amount == Decimal("42000.00") and compliant.part_time_increase_rate == Decimal("0.00")
    assert equal.is_exactly_at_minimum()
    assert low.is_non_compliant() and low.shortfall_amount() == Decimal("0.01")


def test_periodicity_mismatch_is_refused():
    svc = service(grid_version("A", date(2026, 1, 1)))
    with pytest.raises(ValueError, match="La périodicité de la rémunération ne correspond pas à celle du minimum CCNS."):
        svc.evaluate(group(1), date(2026, 1, 1), Decimal("2000.00"), SalaryMinimumPeriodicity.ANNUAL, Decimal("35.00"))
    with pytest.raises(ValueError, match="La périodicité"):
        svc.evaluate(group(7), date(2026, 1, 1), Decimal("42000.00"), SalaryMinimumPeriodicity.MONTHLY, Decimal("35.00"))


@pytest.mark.parametrize("bad", [1, 1.0, "1.00", True])
def test_service_rejects_non_decimal_remuneration_and_hours(bad):
    svc = service(grid_version("A", date(2026, 1, 1)))
    with pytest.raises(TypeError):
        svc.evaluate(group(1), date(2026, 1, 1), bad, SalaryMinimumPeriodicity.MONTHLY, Decimal("35.00"))
    with pytest.raises(TypeError):
        svc.evaluate(group(1), date(2026, 1, 1), Decimal("1.00"), SalaryMinimumPeriodicity.MONTHLY, bad)


def test_service_strict_input_validation_messages():
    svc = service(grid_version("A", date(2026, 1, 1)))
    assert evaluate_monthly(svc, "0.00", "35.00").remuneration_amount == Decimal("0.00")
    with pytest.raises(ValueError, match="Le montant de rémunération ne peut pas être négatif."):
        evaluate_monthly(svc, "-0.01", "35.00")
    with pytest.raises(ValueError, match="La durée hebdomadaire doit être strictement positive."):
        evaluate_monthly(svc, "1.00", "0.00")
    with pytest.raises(ValueError, match="La durée hebdomadaire doit être strictement positive."):
        evaluate_monthly(svc, "1.00", "-1.00")
    with pytest.raises(TypeError):
        svc.evaluate(group(1), datetime(2026, 1, 1), Decimal("1.00"), SalaryMinimumPeriodicity.MONTHLY, Decimal("1.00"))
    with pytest.raises(TypeError):
        svc.evaluate("G1", date(2026, 1, 1), Decimal("1.00"), SalaryMinimumPeriodicity.MONTHLY, Decimal("1.00"))
    with pytest.raises(TypeError):
        SalaryMinimumComplianceService("catalog")
    with pytest.raises(TypeError):
        svc.evaluate(group(1), date(2026, 1, 1), Decimal("1.00"), "monthly", Decimal("1.00"))


def test_result_methods_coherence_uuid_immutability_and_strict_validation():
    result = evaluate_monthly(service(grid_version("A", date(2026, 1, 1))), "2100.00", "35.00")
    assert type(result.id) is UUID
    assert result.has_surplus() and result.surplus_amount() == Decimal("100.00")
    assert not result.has_shortfall() and result.shortfall_amount() == Decimal("0.00")
    with pytest.raises(FrozenInstanceError):
        result.status = SalaryMinimumComplianceStatus.NON_COMPLIANT

    explicit_id = uuid4()
    explicit = SalaryMinimumComplianceResult(**{**{f.name: getattr(result, f.name) for f in result.__dataclass_fields__.values() if f.name != "id"}, "id": explicit_id})
    assert explicit.id == explicit_id

    with pytest.raises(TypeError):
        SalaryMinimumComplianceResult(**{**{f.name: getattr(result, f.name) for f in result.__dataclass_fields__.values() if f.name != "id"}, "id": str(explicit_id)})
    with pytest.raises(ValueError, match="statut"):
        SalaryMinimumComplianceResult(**{**{f.name: getattr(result, f.name) for f in result.__dataclass_fields__.values() if f.name != "status"}, "status": SalaryMinimumComplianceStatus.NON_COMPLIANT})
    with pytest.raises(ValueError, match="différence"):
        SalaryMinimumComplianceResult(**{**{f.name: getattr(result, f.name) for f in result.__dataclass_fields__.values() if f.name != "difference_amount"}, "difference_amount": Decimal("99.99")})
    with pytest.raises(ValueError, match="quantifiés"):
        SalaryMinimumComplianceResult(**{**{f.name: getattr(result, f.name) for f in result.__dataclass_fields__.values() if f.name != "remuneration_amount"}, "remuneration_amount": Decimal("2100.001")})
