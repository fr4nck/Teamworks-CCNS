from datetime import date

import pytest

from application.bootstrap.seed_reference_data import (
    build_default_salary_grid_2026,
    build_default_salary_grid_version_2026,
)
from domain.convention.salary_grid_version import SalaryGridVersion, SalaryGridVersionStatus
from domain.convention.salary_grid_version_selector import SalaryGridVersionSelector
from domain.engine.rule_reference import RuleReference
from domain.engine.rule_version import RuleVersion, RuleVersionStatus, RuleVersionValidationLevel


def make_reference(code: str = "REF_CCNS_MINIMA_TEST") -> RuleReference:
    return RuleReference(code=code, title="Minima CCNS", official_source="Source officielle")


def make_rule_version(reference: RuleReference | None = None) -> RuleVersion:
    reference = reference or make_reference()
    return RuleVersion(
        rule_code="CCNS_MIN_G1_G6_MONTHLY",
        version="2026-01",
        effective_date=date(2026, 1, 1),
        status=RuleVersionStatus.ACTIVE,
        rule_reference=reference,
        validation_level=RuleVersionValidationLevel.DOCUMENTED,
    )


def test_salary_grid_version_requires_stable_identification_and_period():
    with pytest.raises(ValueError):
        SalaryGridVersion(grid_code="", version="2026-01", effective_date=date(2026, 1, 1))

    with pytest.raises(ValueError):
        SalaryGridVersion(
            grid_code="CCNS-2026",
            version="2026-01",
            effective_date=date(2026, 12, 31),
            end_date=date(2026, 1, 1),
        )


def test_salary_grid_version_exposes_rule_version_and_reference_links():
    reference = make_reference("REF_CCNS_MINIMA_2026")
    rule_version = make_rule_version(reference)
    version = SalaryGridVersion(
        grid_code="CCNS-2026",
        version="2026-01",
        effective_date=date(2026, 1, 1),
        status=SalaryGridVersionStatus.ACTIVE,
        rule_version=rule_version,
        validation_level=RuleVersionValidationLevel.DOCUMENTED,
        validation_date=date(2026, 1, 2),
    )

    assert version.rule_version_code == "CCNS_MIN_G1_G6_MONTHLY"
    assert version.rule_reference_code == "REF_CCNS_MINIMA_2026"
    assert version.is_applicable_on(date(2026, 9, 15))


def test_salary_grid_version_selector_returns_version_applicable_to_reference_date():
    old_version = SalaryGridVersion(
        grid_code="CCNS-2026",
        version="2026-01",
        effective_date=date(2026, 1, 1),
        end_date=date(2026, 9, 14),
        status=SalaryGridVersionStatus.ACTIVE,
        validation_level=RuleVersionValidationLevel.DOCUMENTED,
    )
    new_version = SalaryGridVersion(
        grid_code="CCNS-2026",
        version="2026-09",
        effective_date=date(2026, 9, 15),
        status=SalaryGridVersionStatus.SCHEDULED,
        validation_level=RuleVersionValidationLevel.BUSINESS_VALIDATED,
    )
    selector = SalaryGridVersionSelector.from_iterable([old_version, new_version])

    assert selector.require_applicable_version("CCNS-2026", date(2026, 9, 14)) == old_version
    assert selector.require_applicable_version("CCNS-2026", date(2026, 9, 15)) == new_version


def test_future_salary_grid_version_requires_validation_before_selection():
    future_version = SalaryGridVersion(
        grid_code="CCNS-2026",
        version="2026-09-draft",
        effective_date=date(2026, 9, 15),
        status=SalaryGridVersionStatus.SCHEDULED,
        validation_level=RuleVersionValidationLevel.LEGAL_REVIEW_REQUIRED,
    )
    selector = SalaryGridVersionSelector.from_iterable([future_version])

    assert not future_version.is_applicable_on(date(2026, 9, 15))
    assert selector.find_applicable_version("CCNS-2026", date(2026, 9, 15)) is None



def test_scheduled_salary_grid_version_insufficiently_validated_is_not_selected():
    scheduled = SalaryGridVersion(
        grid_code="CCNS-2026",
        version="2026-09-legal-review-required",
        effective_date=date(2026, 9, 15),
        status=SalaryGridVersionStatus.SCHEDULED,
        validation_level=RuleVersionValidationLevel.LEGAL_REVIEW_REQUIRED,
    )
    selector = SalaryGridVersionSelector.from_iterable([scheduled])

    assert selector.find_applicable_version("CCNS-2026", date(2026, 9, 15)) is None


def test_scheduled_salary_grid_version_sufficiently_validated_is_selected():
    scheduled = SalaryGridVersion(
        grid_code="CCNS-2026",
        version="2026-09-business-validated",
        effective_date=date(2026, 9, 15),
        status=SalaryGridVersionStatus.SCHEDULED,
        validation_level=RuleVersionValidationLevel.BUSINESS_VALIDATED,
    )
    selector = SalaryGridVersionSelector.from_iterable([scheduled])

    assert selector.find_applicable_version("CCNS-2026", date(2026, 9, 15)) == scheduled

def test_archived_salary_grid_version_is_not_selected():
    archived = SalaryGridVersion(
        grid_code="CCNS-2026",
        version="2026-01-archive",
        effective_date=date(2026, 1, 1),
        status=SalaryGridVersionStatus.ARCHIVED,
        validation_level=RuleVersionValidationLevel.BUSINESS_VALIDATED,
    )
    selector = SalaryGridVersionSelector.from_iterable([archived])

    assert selector.find_applicable_version("CCNS-2026", date(2026, 9, 15)) is None


def test_default_salary_grid_version_does_not_change_current_grid_amounts():
    grid, lines = build_default_salary_grid_2026()
    version = build_default_salary_grid_version_2026()
    amounts = {line.classification_code: line.amount for line in lines}

    assert version.grid_code == grid.code
    assert version.version == "2026-01"
    assert version.rule_reference_code == "REF_CCNS_MIN_G1_G6_MONTHLY_2026"
    assert amounts["G3"] == 1997.87
    assert amounts["G7"] == 40597.94
