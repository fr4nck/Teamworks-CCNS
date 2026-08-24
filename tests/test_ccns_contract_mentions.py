from decimal import Decimal

from domain.contracts.ccns_contract_mentions import (
    ARTICLE_4_2_1,
    ARTICLE_4_5_2,
    ARTICLE_5_1_5_3,
    CCNSContractComplianceService,
    ContractMentionCode,
    ContractTermsSnapshot,
)
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization


def _base_values():
    return {
        ContractMentionCode.CONTRACT_NATURE: "CDI",
        ContractMentionCode.EMPLOYER_LEGAL_NAME: "Pêle-Mêle Sports et Loisirs",
        ContractMentionCode.EMPLOYER_ADDRESS: "4 rue des Deux Gares",
        ContractMentionCode.EMPLOYEE_LAST_NAME: "Dupont",
        ContractMentionCode.EMPLOYEE_FIRST_NAME: "Sophie",
        ContractMentionCode.EMPLOYEE_NATIONALITY: "Française",
        ContractMentionCode.EMPLOYEE_IDENTIFICATION: "NIR renseigné",
        ContractMentionCode.HIRE_DATE: "2026-09-01",
        ContractMentionCode.WORKPLACE: "La Guerche-de-Bretagne",
        ContractMentionCode.JOB_TITLE: "Animatrice",
        ContractMentionCode.CCNS_CLASSIFICATION_GROUP: "G1",
        ContractMentionCode.BASE_SALARY: "1848.42",
        ContractMentionCode.REMUNERATION_COMPONENTS: "Salaire de base ; autres éléments : néant",
        ContractMentionCode.REFERENCE_WORKING_TIME: "35 h",
        ContractMentionCode.SPECIAL_WORKING_CONDITIONS: "Néant",
        ContractMentionCode.WEEKLY_REST_TERMS: "Repos hebdomadaire précisé",
        ContractMentionCode.BENEFITS_IN_KIND: "Néant",
        ContractMentionCode.TRIAL_PERIOD_TERMS: "1 mois",
        ContractMentionCode.SOCIAL_SECURITY_BODY: "URSSAF",
        ContractMentionCode.SOCIAL_SECURITY_REGISTRATION: "Référence employeur",
        ContractMentionCode.RETIREMENT_FUND: "Caisse retraite",
        ContractMentionCode.WELFARE_FUND: "Organisme prévoyance",
        ContractMentionCode.COLLECTIVE_AGREEMENT_REFERENCE: "Convention collective nationale du sport",
        ContractMentionCode.COLLECTIVE_AGREEMENT_CONSULTATION: "Consultable au siège",
    }


def _snapshot(*, weekly_hours=Decimal("35.00"), work_ratio=Decimal("1.00"), contract_type=ContractType.CDI, regime=EmploymentRegime.CCNS_STANDARD, time_organization=TimeOrganization.WEEKLY_CONSTANT, foreign=False, values=None):
    return ContractTermsSnapshot(
        contract_type=contract_type,
        employment_regime=regime,
        time_organization=time_organization,
        weekly_reference_hours=weekly_hours,
        work_ratio=work_ratio,
        is_foreign_worker=foreign,
        values=_base_values() if values is None else values,
    )


def test_full_time_standard_contract_is_compliant_when_base_mentions_are_present():
    result = CCNSContractComplianceService().evaluate(_snapshot())
    assert result.applicable is True
    assert result.is_compliant
    assert result.missing_codes == ()
    assert {item.source_reference for item in result.requirements} == {ARTICLE_4_2_1}


def test_missing_base_mentions_are_reported_with_stable_codes():
    values = _base_values()
    values[ContractMentionCode.CCNS_CLASSIFICATION_GROUP] = "  "
    values.pop(ContractMentionCode.WEEKLY_REST_TERMS)

    result = CCNSContractComplianceService().evaluate(_snapshot(values=values))

    assert not result.is_compliant
    assert result.missing_codes == (
        ContractMentionCode.CCNS_CLASSIFICATION_GROUP,
        ContractMentionCode.WEEKLY_REST_TERMS,
    )


def test_foreign_worker_requires_work_authorization_but_french_worker_does_not():
    service = CCNSContractComplianceService()
    french = service.evaluate(_snapshot(foreign=False))
    foreign = service.evaluate(_snapshot(foreign=True))

    assert ContractMentionCode.WORK_AUTHORIZATION not in french.missing_codes
    assert ContractMentionCode.WORK_AUTHORIZATION in foreign.missing_codes

    values = _base_values()
    values[ContractMentionCode.WORK_AUTHORIZATION] = "Titre autorisant le travail n° X"
    foreign_complete = service.evaluate(_snapshot(foreign=True, values=values))
    assert foreign_complete.is_compliant


def test_part_time_contract_adds_article_5_1_5_3_requirements():
    service = CCNSContractComplianceService()
    result = service.evaluate(_snapshot(weekly_hours=Decimal("21.00"), work_ratio=Decimal("0.60")))

    missing_from_part_time = result.missing_from_source(ARTICLE_5_1_5_3)
    assert len(missing_from_part_time) == 9
    assert ContractMentionCode.PART_TIME_REFERENCE_PERIOD in result.missing_codes
    assert ContractMentionCode.PART_TIME_COMPLEMENTARY_HOURS_LIMITS in result.missing_codes
    assert ContractMentionCode.PART_TIME_PLANNING_DELIVERY_DEADLINE in result.missing_codes

    values = _base_values()
    for requirement in service.requirements_for(_snapshot(weekly_hours=Decimal("21.00"), work_ratio=Decimal("0.60"))):
        if requirement.source_reference == ARTICLE_5_1_5_3:
            values[requirement.code] = "Clause renseignée"
    complete = service.evaluate(_snapshot(weekly_hours=Decimal("21.00"), work_ratio=Decimal("0.60"), values=values))
    assert complete.is_compliant


def test_cdii_adds_article_4_5_2_requirements():
    service = CCNSContractComplianceService()
    snapshot = _snapshot(
        weekly_hours=Decimal("20.00"),
        work_ratio=Decimal("0.57"),
        contract_type=ContractType.CDII,
        regime=EmploymentRegime.CCNS_CDII,
        time_organization=TimeOrganization.INTERMITTENCE,
    )
    requirements = service.requirements_for(snapshot)

    cdii_codes = {item.code for item in requirements if item.source_reference == ARTICLE_4_5_2}
    assert cdii_codes == {
        ContractMentionCode.CDII_MINIMUM_ANNUAL_WORKING_TIME,
        ContractMentionCode.CDII_WORK_PERIODS,
        ContractMentionCode.CDII_HOURS_WITHIN_PERIODS,
        ContractMentionCode.CDII_PERIOD_MODIFICATION_CONDITIONS,
        ContractMentionCode.CDII_ANNUAL_CYCLE_START_DATE,
    }


def test_work_ratio_can_detect_part_time_when_weekly_hours_are_unknown():
    result = CCNSContractComplianceService().evaluate(_snapshot(weekly_hours=None, work_ratio=Decimal("0.80")))
    assert ContractMentionCode.PART_TIME_REFERENCE_PERIOD in result.missing_codes


def test_cee_is_explicitly_outside_standard_ccns_contract_mentions_scope():
    result = CCNSContractComplianceService().evaluate(
        _snapshot(
            contract_type=ContractType.CEE,
            regime=EmploymentRegime.CEE,
            time_organization=TimeOrganization.DAILY_CEE,
        )
    )
    assert result.applicable is False
    assert result.requirements == ()
    assert result.missing_codes == ()


def test_work_ratio_above_one_is_rejected_as_invalid_contract_ratio():
    import pytest

    with pytest.raises(ValueError):
        _snapshot(work_ratio=Decimal("1.01"))


def test_unknown_foreign_worker_status_prevents_false_green_compliance():
    result = CCNSContractComplianceService().evaluate(_snapshot(foreign=None))
    assert result.missing_codes == ()
    assert result.unresolved_conditional_codes == (ContractMentionCode.WORK_AUTHORIZATION,)
    assert result.is_compliant is False
