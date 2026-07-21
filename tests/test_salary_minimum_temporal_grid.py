from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.convention import (
    CCNSClassification,
    PartTimeMinimumIncreaseRule,
    SalaryGridCatalog,
    SalaryGridEntry,
    SalaryGridVersion,
    SalaryMinimumPeriodicity,
    create_ccns_part_time_minimum_increase_rules,
    create_ccns_salary_grid_2026_01,
    increase_rate_for_weekly_hours,
)


def group(number: int) -> CCNSClassification:
    return CCNSClassification(code=f"G{number}", label=f"Groupe {number}")


def entry(number: int, amount: str = "2000.005") -> SalaryGridEntry:
    periodicity = SalaryMinimumPeriodicity.MONTHLY if number <= 6 else SalaryMinimumPeriodicity.ANNUAL
    return SalaryGridEntry(group(number), Decimal(amount), periodicity)


def version(code: str, start: date, end: date | None = None) -> SalaryGridVersion:
    return SalaryGridVersion(code, code, start, (entry(1),), effective_until=end)


@pytest.mark.parametrize("number", [1, 7])
def test_salary_grid_entry_valid_periodicities(number):
    item = entry(number)
    assert item.amount == Decimal("2000.01")
    assert item.is_monthly() is (number == 1)
    assert item.is_annual() is (number == 7)
    assert type(item.id) is UUID


@pytest.mark.parametrize("amount", [0, 1.0, "1.00", True])
def test_salary_grid_entry_requires_strict_decimal(amount):
    with pytest.raises((TypeError, ValueError)):
        SalaryGridEntry(group(1), amount, SalaryMinimumPeriodicity.MONTHLY)


def test_salary_grid_entry_validates_amount_periodicity_group_and_uuid():
    with pytest.raises(ValueError):
        SalaryGridEntry(group(1), Decimal("-1"), SalaryMinimumPeriodicity.MONTHLY)
    with pytest.raises(TypeError):
        SalaryGridEntry("G1", Decimal("1"), SalaryMinimumPeriodicity.MONTHLY)
    with pytest.raises(TypeError):
        SalaryGridEntry(group(1), Decimal("1"), "monthly")
    explicit_id = uuid4()
    assert SalaryGridEntry(group(1), Decimal("1"), SalaryMinimumPeriodicity.MONTHLY, id=explicit_id).id == explicit_id
    with pytest.raises(TypeError):
        SalaryGridEntry(group(1), Decimal("1"), SalaryMinimumPeriodicity.MONTHLY, id=str(explicit_id))
    with pytest.raises(FrozenInstanceError):
        entry(1).amount = Decimal("3")


def test_salary_grid_version_normalizes_and_preserves_order():
    entries = (entry(2), entry(1))
    item = SalaryGridVersion(
        " ccns-test ",
        " Grille test ",
        date(2026, 1, 1),
        entries,
        source_reference=" Source ",
    )
    assert item.code == "CCNS-TEST"
    assert item.name == "Grille test"
    assert item.source_reference == "Source"
    assert item.entries == entries
    assert item.entry_count() == 2
    assert item.is_active() and item.is_open_ended()
    assert item.amount_for_group(group(1)) == Decimal("2000.01")
    assert item.contains_group(group(2))
    with pytest.raises(ValueError, match="groupe demandé"):
        item.entry_for_group(group(3))


def test_salary_grid_version_strict_validation_and_periodicity():
    with pytest.raises(TypeError):
        SalaryGridVersion("A", "A", datetime(2026, 1, 1), (entry(1),))
    with pytest.raises(TypeError):
        SalaryGridVersion("A", "A", date(2026, 1, 1), [entry(1)])
    with pytest.raises(ValueError):
        SalaryGridVersion("A", "A", date(2026, 1, 1), ())
    with pytest.raises(ValueError):
        SalaryGridVersion("A", "A", date(2026, 2, 1), (entry(1),), effective_until=date(2026, 1, 1))
    with pytest.raises(ValueError):
        SalaryGridVersion("A", "A", date(2026, 1, 1), (entry(1), entry(1)))
    with pytest.raises(ValueError):
        SalaryGridVersion(
            "A", "A", date(2026, 1, 1),
            (SalaryGridEntry(group(1), Decimal("1"), SalaryMinimumPeriodicity.ANNUAL),),
        )
    with pytest.raises(ValueError):
        SalaryGridVersion(
            "A", "A", date(2026, 1, 1),
            (SalaryGridEntry(group(7), Decimal("1"), SalaryMinimumPeriodicity.MONTHLY),),
        )
    with pytest.raises(TypeError):
        SalaryGridVersion("A", "A", date(2026, 1, 1), (entry(1),), active=1)


def test_salary_grid_version_applies_on_inclusive_boundaries():
    item = version("A", date(2026, 1, 1), date(2026, 12, 31))
    assert item.applies_on(date(2026, 1, 1))
    assert item.applies_on(date(2026, 12, 31))
    assert not item.applies_on(date(2025, 12, 31))
    with pytest.raises(TypeError):
        item.applies_on(datetime(2026, 1, 1))
    with pytest.raises(FrozenInstanceError):
        item.code = "B"


def test_catalog_selects_successive_versions_and_accepts_gap():
    first = version("A", date(2025, 1, 1), date(2025, 6, 30))
    second = version("B", date(2026, 1, 1))
    catalog = SalaryGridCatalog((first, second))
    assert catalog.version_count() == 2
    assert catalog.version_applicable_on(date(2025, 6, 30)) is first
    assert catalog.version_applicable_on(date(2026, 1, 1)) is second
    assert not catalog.has_version_for(date(2025, 9, 1))
    with pytest.raises(ValueError, match="Aucune grille"):
        catalog.version_applicable_on(date(2025, 9, 1))
    assert catalog.entry_for(group(1), date(2026, 1, 1)) is second.entries[0]
    assert catalog.amount_for(group(1), date(2026, 1, 1)) == Decimal("2000.01")


def test_catalog_rejects_invalid_collections_duplicates_and_overlap():
    first = version("A", date(2026, 1, 1), date(2026, 12, 31))
    overlapping = version("B", date(2026, 7, 1))
    with pytest.raises(TypeError):
        SalaryGridCatalog([first])
    with pytest.raises(ValueError):
        SalaryGridCatalog(())
    with pytest.raises(ValueError, match="chevaucher"):
        SalaryGridCatalog((first, overlapping))
    with pytest.raises(ValueError, match="codes"):
        SalaryGridCatalog((first, version("A", date(2027, 1, 1))))
    duplicate_id = SalaryGridVersion("C", "C", date(2027, 1, 1), (entry(1),), id=first.id)
    with pytest.raises(ValueError, match="UUID"):
        SalaryGridCatalog((first, duplicate_id))
    with pytest.raises(FrozenInstanceError):
        SalaryGridCatalog((first,)).versions = ()


def test_ccns_2026_factory_contains_exact_data_and_returns_new_instances():
    grid = create_ccns_salary_grid_2026_01()
    other = create_ccns_salary_grid_2026_01()
    expected = {
        "G1": Decimal("1848.42"), "G2": Decimal("1885.14"),
        "G3": Decimal("1997.87"), "G4": Decimal("2099.37"),
        "G5": Decimal("2333.99"), "G6": Decimal("2865.97"),
        "G7": Decimal("40597.94"), "G8": Decimal("46833.81"),
    }
    assert grid.effective_from == date(2026, 1, 1)
    assert grid.is_open_ended()
    assert grid.source_reference
    assert grid.id != other.id
    assert {item.classification_group.code: item.amount for item in grid.entries} == expected
    assert all(item.is_monthly() for item in grid.entries[:6])
    assert all(item.is_annual() for item in grid.entries[6:])


@pytest.mark.parametrize(
    ("hours", "rate"),
    [("10.00", "0.05"), ("10.01", "0.02"), ("23.99", "0.02"), ("24.00", "0.00"), ("35.00", "0.00")],
)
def test_part_time_increase_rate_boundaries(hours, rate):
    assert increase_rate_for_weekly_hours(Decimal(hours)) == Decimal(rate)


@pytest.mark.parametrize("hours", [Decimal("0"), Decimal("-1"), 10, 10.0, "10", True])
def test_part_time_increase_rate_requires_positive_strict_decimal(hours):
    with pytest.raises((TypeError, ValueError)):
        increase_rate_for_weekly_hours(hours)


def test_part_time_rules_are_stable_and_immutable():
    rules = create_ccns_part_time_minimum_increase_rules()
    assert tuple(rule.increase_rate for rule in rules) == (Decimal("0.05"), Decimal("0.02"))
    assert type(rules[0]) is PartTimeMinimumIncreaseRule
    with pytest.raises(FrozenInstanceError):
        rules[0].increase_rate = Decimal("0")
