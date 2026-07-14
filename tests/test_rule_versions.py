from datetime import date

import pytest

from domain.engine.default_rules_ccns import build_default_ccns_rules
from domain.engine.rule_reference import RuleReference
from domain.engine.rule_version import RuleVersion, RuleVersionStatus, RuleVersionValidationLevel
from domain.engine.rule_version_selector import RuleVersionSelector


def make_reference(code: str = "REF_TEST") -> RuleReference:
    return RuleReference(code=code, title="Règle test", official_source="Source officielle")


def test_rule_version_requires_stable_identification_and_period():
    with pytest.raises(ValueError):
        RuleVersion(rule_code="", version="2026-01", effective_date=date(2026, 1, 1))

    with pytest.raises(ValueError):
        RuleVersion(
            rule_code="SENIORITY_G1_G6",
            version="2026-01",
            effective_date=date(2026, 12, 31),
            end_date=date(2026, 1, 1),
        )


def test_rule_version_exposes_regulatory_reference_link():
    reference = make_reference("REF_CCNS_SENIORITY_G1_G6_2026")
    version = RuleVersion(
        rule_code="SENIORITY_G1_G6",
        version="2026-01",
        effective_date=date(2026, 1, 1),
        status=RuleVersionStatus.ACTIVE,
        rule_reference=reference,
        validation_level=RuleVersionValidationLevel.DOCUMENTED,
    )

    assert version.rule_reference_code == "REF_CCNS_SENIORITY_G1_G6_2026"
    assert version.is_applicable_on(date(2026, 9, 15))


def test_rule_version_selector_returns_version_applicable_to_reference_date():
    reference = make_reference()
    old_version = RuleVersion(
        rule_code="SENIORITY_G1_G6",
        version="2026-01",
        effective_date=date(2026, 1, 1),
        end_date=date(2026, 9, 14),
        status=RuleVersionStatus.ACTIVE,
        rule_reference=reference,
        validation_level=RuleVersionValidationLevel.DOCUMENTED,
    )
    new_version = RuleVersion(
        rule_code="SENIORITY_G1_G6",
        version="2026-09",
        effective_date=date(2026, 9, 15),
        status=RuleVersionStatus.SCHEDULED,
        comment="Préparation d'une future version sans activation de calcul dans cette PR.",
        rule_reference=reference,
        validation_level=RuleVersionValidationLevel.BUSINESS_VALIDATED,
    )
    selector = RuleVersionSelector.from_iterable([old_version, new_version])

    assert selector.require_applicable_version("SENIORITY_G1_G6", date(2026, 9, 14)) == old_version
    assert selector.require_applicable_version("SENIORITY_G1_G6", date(2026, 9, 15)) == new_version


def test_scheduled_rule_version_requires_sufficient_validation_before_selection():
    scheduled = RuleVersion(
        rule_code="SENIORITY_G1_G6",
        version="2026-09",
        effective_date=date(2026, 9, 15),
        status=RuleVersionStatus.SCHEDULED,
        rule_reference=make_reference(),
        validation_level=RuleVersionValidationLevel.LEGAL_REVIEW_REQUIRED,
    )
    selector = RuleVersionSelector.from_iterable([scheduled])

    assert not scheduled.is_applicable_on(date(2026, 9, 15))
    assert selector.find_applicable_version("SENIORITY_G1_G6", date(2026, 9, 15)) is None


def test_rule_version_selector_ignores_drafts_for_applicable_date():
    draft = RuleVersion(
        rule_code="SENIORITY_G1_G6",
        version="2026-09-draft",
        effective_date=date(2026, 9, 15),
        status=RuleVersionStatus.DRAFT,
        rule_reference=make_reference(),
    )
    selector = RuleVersionSelector.from_iterable([draft])

    assert selector.find_applicable_version("SENIORITY_G1_G6", date(2026, 9, 15)) is None


def test_default_seniority_rule_exposes_initial_rule_version_without_changing_parameters():
    rules = {rule.code: rule for rule in build_default_ccns_rules()}

    seniority = rules["SENIORITY_G1_G6"]
    selector = RuleVersionSelector.from_iterable(seniority.rule_versions)
    version = selector.require_applicable_version("SENIORITY_G1_G6", date(2026, 9, 15))

    assert version.version == "2026-01"
    assert version.rule_reference_code == "REF_CCNS_SENIORITY_G1_G6_2026"
    assert seniority.parameters["percent_per_step"] == 1.0
    assert seniority.parameters["max_percent"] == 15.0
