from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.convention import (
    ApplicableSalaryMinimumResult,
    ApplicableSalaryMinimumService,
    ApplicableSalaryMinimumSource,
    ApplicableSalaryMinimumStatus,
    CCNSClassification,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumComplianceService,
    SalaryMinimumPeriodicity,
    SmicCatalog,
    SmicTerritory,
    SmicVersion,
)


def group(number: int) -> CCNSClassification:
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def grid_version(code: str, start: date, end: date | None = None, g1: str = "2000.00", g7: str = "42000.00") -> SalaryGridVersion:
    return SalaryGridVersion(
        code,
        code,
        start,
        (
            SalaryGridEntry(group(1), Decimal(g1), SalaryMinimumPeriodicity.MONTHLY),
            SalaryGridEntry(group(7), Decimal(g7), SalaryMinimumPeriodicity.ANNUAL),
            SalaryGridEntry(group(8), Decimal("47000.00"), SalaryMinimumPeriodicity.ANNUAL),
        ),
        effective_until=end,
    )


def smic(code: str, territory: SmicTerritory, start: date, end: date | None, monthly: str) -> SmicVersion:
    return SmicVersion(code, code, territory, start, end, Decimal("10.00"), Decimal(monthly), Decimal("35.00"), "test")


def service(grid_versions: tuple[SalaryGridVersion, ...], smic_versions: tuple[SmicVersion, ...]) -> ApplicableSalaryMinimumService:
    return ApplicableSalaryMinimumService(SalaryMinimumComplianceService(SalaryGridCatalog(grid_versions)), SmicCatalog(smic_versions))


def evaluate(svc: ApplicableSalaryMinimumService, amount="3000.00", hours="35.00", ref=date(2026, 6, 1), territory=SmicTerritory.METROPOLITAN_FRANCE, cls=None):
    return svc.evaluate(cls or group(1), ref, territory, Decimal(amount), Decimal(hours))


def result_kwargs(result: ApplicableSalaryMinimumResult, **overrides):
    values = {name: getattr(result, name) for name in result.__dataclass_fields__ if name != "id"}
    values.update(overrides)
    return values


def test_temporal_selection_for_ccns_grid_and_smic_territories():
    first_grid = grid_version("G-A", date(2026, 1, 1), date(2026, 5, 31), "1800.00")
    second_grid = grid_version("G-B", date(2026, 6, 1), None, "1900.00")
    metro_may = smic("S-MET-05", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), date(2026, 5, 31), "1823.03")
    metro_june = smic("S-MET-06", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 6, 1), None, "1867.02")
    mayotte_may = smic("S-MAY-05", SmicTerritory.MAYOTTE, date(2026, 1, 1), date(2026, 5, 31), "1415.05")
    mayotte_june = smic("S-MAY-06", SmicTerritory.MAYOTTE, date(2026, 6, 1), None, "1449.93")
    svc = service((first_grid, second_grid), (metro_may, metro_june, mayotte_may, mayotte_june))

    assert evaluate(svc, ref=date(2026, 5, 31)).ccns_compliance_result.salary_grid_version is first_grid
    assert evaluate(svc, ref=date(2026, 5, 31)).smic_version is metro_may
    assert evaluate(svc, ref=date(2026, 6, 1)).ccns_compliance_result.salary_grid_version is second_grid
    assert evaluate(svc, ref=date(2026, 6, 1)).smic_version is metro_june
    assert evaluate(svc, ref=date(2026, 6, 1), territory=SmicTerritory.MAYOTTE).smic_version is mayotte_june


def test_missing_grid_or_smic_errors_are_propagated():
    svc = service((grid_version("G", date(2026, 1, 1), date(2026, 1, 31)),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "1000.00"),))
    with pytest.raises(ValueError, match="Aucune grille"):
        evaluate(svc, ref=date(2026, 2, 1))
    svc_no_smic = service((grid_version("G", date(2026, 1, 1), None),), (smic("S", SmicTerritory.MAYOTTE, date(2026, 1, 1), None, "1000.00"),))
    with pytest.raises(ValueError, match="Aucune version du SMIC"):
        evaluate(svc_no_smic)


@pytest.mark.parametrize(("remuneration", "status", "difference"), [("2100.00", ApplicableSalaryMinimumStatus.COMPLIANT, "100.00"), ("2000.00", ApplicableSalaryMinimumStatus.COMPLIANT, "0.00"), ("1999.99", ApplicableSalaryMinimumStatus.NON_COMPLIANT, "-0.01")])
def test_ccns_minimum_higher_than_smic_drives_final_status(remuneration, status, difference):
    result = evaluate(service((grid_version("G", date(2026, 1, 1), g1="2000.00"),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "1800.00"),)), amount=remuneration)
    assert result.source is ApplicableSalaryMinimumSource.CCNS
    assert result.required_minimum_amount == Decimal("2000.00")
    assert result.status is status
    assert result.difference_amount == Decimal(difference)


def test_smic_minimum_higher_can_make_ccns_compliant_remuneration_non_compliant():
    result = evaluate(service((grid_version("G", date(2026, 1, 1), g1="1800.00"),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),)), amount="1850.00")
    assert result.ccns_compliance_result.is_compliant()
    assert result.is_non_compliant()
    assert result.source is ApplicableSalaryMinimumSource.SMIC
    assert result.required_minimum_amount == Decimal("2000.00")
    assert result.shortfall_amount() == Decimal("150.00")


def test_equal_minimums_and_result_methods():
    result = evaluate(service((grid_version("G", date(2026, 1, 1), g1="2000.00"),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),)), amount="2000.00")
    assert result.are_minimums_equal() and not result.is_ccns_minimum() and not result.is_smic_minimum()
    assert result.is_exactly_at_minimum() and result.required_increase_amount() == Decimal("0.00")
    low = evaluate(service((grid_version("G2", date(2026, 1, 1), g1="2000.00"),), (smic("S2", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),)), amount="1990.00")
    assert low.are_minimums_equal() and low.required_increase_amount() == Decimal("10.00")


@pytest.mark.parametrize(("hours", "smic_required"), [("34.00", "1942.86"), ("24.00", "1371.43"), ("23.99", "1370.86"), ("10.00", "571.43"), ("9.99", "570.86"), ("33.333", "1904.74")])
def test_part_time_smic_proration_without_ccns_increase(hours, smic_required):
    result = evaluate(service((grid_version("G", date(2026, 1, 1), g1="2000.00"),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),)), hours=hours)
    assert result.smic_required_minimum_amount == Decimal(smic_required)
    if Decimal(hours) < Decimal("24.00"):
        assert result.ccns_compliance_result.part_time_increase_rate > Decimal("0.00")


@pytest.mark.parametrize("hours", ["35.00", "39.00"])
def test_full_time_and_more_than_full_time_do_not_increase_monthly_smic(hours):
    result = evaluate(service((grid_version("G", date(2026, 1, 1), g1="1800.00"),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),)), hours=hours)
    assert result.smic_required_minimum_amount == Decimal("2000.00")


@pytest.mark.parametrize("cls", [group(7), group(8)])
def test_annual_groups_are_refused_with_business_message(cls):
    with pytest.raises(ValueError, match="Le contrôle du minimum le plus favorable est limité aux minima CCNS mensuels."):
        evaluate(service((grid_version("G", date(2026, 1, 1)),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),)), cls=cls)


@pytest.mark.parametrize("bad", [1, 1.0, "1.00", True])
def test_strict_decimal_inputs(bad):
    svc = service((grid_version("G", date(2026, 1, 1)),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),))
    with pytest.raises(TypeError):
        svc.evaluate(group(1), date(2026, 1, 1), SmicTerritory.METROPOLITAN_FRANCE, bad, Decimal("35.00"))
    with pytest.raises(TypeError):
        svc.evaluate(group(1), date(2026, 1, 1), SmicTerritory.METROPOLITAN_FRANCE, Decimal("1.00"), bad)


def test_strict_input_validation_messages_and_constructor_types():
    svc = service((grid_version("G", date(2026, 1, 1)),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),))
    assert evaluate(svc, amount="0.00").remuneration_amount == Decimal("0.00")
    with pytest.raises(ValueError, match="Le montant de rémunération ne peut pas être négatif."):
        evaluate(svc, amount="-0.01")
    for hours in ("0.00", "-1.00"):
        with pytest.raises(ValueError, match="La durée hebdomadaire doit être strictement positive."):
            evaluate(svc, hours=hours)
    with pytest.raises(TypeError):
        svc.evaluate(group(1), datetime(2026, 1, 1), SmicTerritory.METROPOLITAN_FRANCE, Decimal("1.00"), Decimal("1.00"))
    with pytest.raises(TypeError):
        svc.evaluate("G1", date(2026, 1, 1), SmicTerritory.METROPOLITAN_FRANCE, Decimal("1.00"), Decimal("1.00"))
    with pytest.raises(TypeError):
        svc.evaluate(group(1), date(2026, 1, 1), "metro", Decimal("1.00"), Decimal("1.00"))
    with pytest.raises(TypeError):
        ApplicableSalaryMinimumService("svc", svc.smic_catalog)
    with pytest.raises(TypeError):
        ApplicableSalaryMinimumService(svc.salary_minimum_compliance_service, "catalog")


def test_result_uuid_immutability_methods_and_strict_coherence():
    result = evaluate(service((grid_version("G", date(2026, 1, 1), g1="1800.00"),), (smic("S", SmicTerritory.METROPOLITAN_FRANCE, date(2026, 1, 1), None, "2000.00"),)), amount="2100.00")
    assert type(result.id) is UUID
    assert result.has_surplus() and result.surplus_amount() == Decimal("100.00")
    assert not result.has_shortfall() and result.shortfall_amount() == Decimal("0.00")
    with pytest.raises(FrozenInstanceError):
        result.status = ApplicableSalaryMinimumStatus.NON_COMPLIANT
    explicit_id = uuid4()
    assert ApplicableSalaryMinimumResult(**result_kwargs(result), id=explicit_id).id == explicit_id
    with pytest.raises(TypeError):
        ApplicableSalaryMinimumResult(**result_kwargs(result), id=str(explicit_id))
    with pytest.raises(ValueError, match="quantifiés"):
        ApplicableSalaryMinimumResult(**result_kwargs(result, remuneration_amount=Decimal("2100.001")))
    with pytest.raises(ValueError, match="minimum exigé"):
        ApplicableSalaryMinimumResult(**result_kwargs(result, required_minimum_amount=Decimal("1800.00")))
    with pytest.raises(ValueError, match="source"):
        ApplicableSalaryMinimumResult(**result_kwargs(result, source=ApplicableSalaryMinimumSource.CCNS))
    with pytest.raises(ValueError, match="différence"):
        ApplicableSalaryMinimumResult(**result_kwargs(result, difference_amount=Decimal("99.99")))
    with pytest.raises(ValueError, match="statut"):
        ApplicableSalaryMinimumResult(**result_kwargs(result, status=ApplicableSalaryMinimumStatus.NON_COMPLIANT))
    with pytest.raises(ValueError, match="résultat CCNS"):
        ApplicableSalaryMinimumResult(**result_kwargs(result, ccns_minimum_amount=Decimal("1800.01")))
    other_smic = smic("S2", SmicTerritory.MAYOTTE, date(2026, 1, 1), None, "2000.00")
    with pytest.raises(ValueError, match="territoire"):
        ApplicableSalaryMinimumResult(**result_kwargs(result, smic_version=other_smic))
