from decimal import Decimal

import pytest

from domain.contracts.contract_creation_rules import (
    CEEQualification,
    ContractCreationContext,
    ContractCreationRules,
    ConventionCode,
)
from domain.contracts.contract_type import ContractType


def test_cee_requires_qualification_and_rejects_ccns_classification():
    rules = ContractCreationRules()
    errors = rules.validate_context(
        ContractCreationContext(
            convention=ConventionCode.CCNS,
            contract_type=ContractType.CEE,
            classification_code="G1",
        )
    )

    assert "La qualification CEE est obligatoire." in errors
    assert "Un CEE ne doit pas utiliser une classification conventionnelle CCNS." in errors


def test_non_cee_rejects_cee_qualification():
    rules = ContractCreationRules()
    errors = rules.validate_context(
        ContractCreationContext(
            convention=ConventionCode.CCNS,
            contract_type=ContractType.CDD,
            classification_code="G2",
            cee_qualification=CEEQualification.BAFA_HOLDER,
        )
    )

    assert errors == ("La qualification CEE n'est autorisée que pour un contrat CEE.",)


def test_ccns_standard_contract_requires_classification():
    rules = ContractCreationRules()
    errors = rules.validate_context(
        ContractCreationContext(
            convention=ConventionCode.CCNS,
            contract_type=ContractType.CDI,
        )
    )

    assert errors == ("La classification CCNS est obligatoire pour ce contrat.",)


def test_cee_distinguishes_holder_and_trainee_employer_rates():
    rules = ContractCreationRules(
        cee_employer_daily_rates={
            CEEQualification.BAFA_HOLDER: Decimal("65.00"),
            CEEQualification.BAFA_TRAINEE: Decimal("52.00"),
        }
    )

    holder = rules.resolve_cee_daily_rate(
        CEEQualification.BAFA_HOLDER,
        legal_minimum_daily_rate=Decimal("50.00"),
    )
    trainee = rules.resolve_cee_daily_rate(
        CEEQualification.BAFA_TRAINEE,
        legal_minimum_daily_rate=Decimal("50.00"),
    )

    assert holder.employer_daily_rate == Decimal("65.00")
    assert trainee.employer_daily_rate == Decimal("52.00")
    assert holder.compliant is True
    assert trainee.compliant is True


def test_cee_rate_below_legal_minimum_is_flagged_and_effective_rate_is_safe_floor():
    rules = ContractCreationRules(
        cee_employer_daily_rates={CEEQualification.BAFA_TRAINEE: Decimal("45.00")}
    )

    decision = rules.resolve_cee_daily_rate(
        CEEQualification.BAFA_TRAINEE,
        legal_minimum_daily_rate=Decimal("50.00"),
    )

    assert decision.compliant is False
    assert decision.effective_daily_rate == Decimal("50.00")
    assert decision.messages == (
        "Le barème employeur est inférieur au minimum légal CEE applicable.",
    )


def test_missing_cee_employer_rate_is_not_silently_accepted():
    decision = ContractCreationRules().resolve_cee_daily_rate(
        CEEQualification.UNQUALIFIED,
        legal_minimum_daily_rate=Decimal("50.00"),
    )

    assert decision.compliant is False
    assert decision.effective_daily_rate == Decimal("50.00")
    assert "Aucun barème employeur CEE" in decision.messages[0]


def test_classification_family_depends_on_convention_and_disappears_for_cee():
    rules = ContractCreationRules()

    assert rules.allowed_classification_family(
        ContractCreationContext(ConventionCode.CCNS, ContractType.CDI)
    ) == "CCNS_GROUPS"
    assert rules.allowed_classification_family(
        ContractCreationContext(ConventionCode.ECLAT, ContractType.CDI)
    ) == "ECLAT_CLASSIFICATIONS"
    assert rules.allowed_classification_family(
        ContractCreationContext(ConventionCode.CENTRES_SOCIAUX, ContractType.CDI)
    ) == "CENTRES_SOCIAUX_CLASSIFICATIONS"
    assert rules.allowed_classification_family(
        ContractCreationContext(
            ConventionCode.CCNS,
            ContractType.CEE,
            cee_qualification=CEEQualification.BAFA_HOLDER,
        )
    ) is None


def test_legal_minimum_must_be_decimal():
    with pytest.raises(TypeError):
        ContractCreationRules().resolve_cee_daily_rate(
            CEEQualification.BAFA_HOLDER,
            legal_minimum_daily_rate=50.0,
        )
