from datetime import date

import pytest

from domain.engine.default_rules_ccns import build_default_ccns_rules
from domain.engine.rule_reference import RuleReference, RuleReferenceStatus


def test_rule_reference_requires_stable_identification():
    with pytest.raises(ValueError):
        RuleReference(code="", title="Minima", official_source="Légifrance")


def test_rule_reference_validity_period_and_explanation():
    reference = RuleReference(
        code="REF_TEST",
        title="Règle test",
        official_source="Source officielle",
        official_url="https://example.invalid/regle",
        legal_reference="article test",
        effective_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=RuleReferenceStatus.VERIFIED,
    )

    assert reference.is_valid_on(date(2026, 7, 1))
    assert not reference.is_valid_on(date(2027, 1, 1))
    assert reference.explanation() == "Cette règle provient de Source officielle, article test (https://example.invalid/regle)."


def test_default_ccns_rules_expose_initial_regulatory_references():
    rules = {rule.code: rule for rule in build_default_ccns_rules()}

    seniority = rules["SENIORITY_G1_G6"]
    assert seniority.rule_reference is not None
    assert seniority.rule_reference.code == "REF_CCNS_SENIORITY_G1_G6_2026"

    minimum = rules["CCNS_MIN_G1_G6_MONTHLY"]
    assert minimum.rule_reference is not None
    assert minimum.rule_reference.official_url == "https://www.legifrance.gouv.fr/conv_coll/id/KALICONT000017577652"
