from datetime import date

from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization
from domain.engine.legal_certainty import LegalCertainty
from domain.engine.seniority import check_ccns_seniority_amount


def test_seniority_amount_exposes_majority_legal_certainty_without_changing_amounts():
    contract = Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2020, 1, 1),
        ccns_classification_code="G3",
    )

    result, anomaly = check_ccns_seniority_amount(
        contract=contract,
        reference_date=date(2026, 1, 1),
        smc_group_3_amount=2000.0,
        actual_seniority_amount=180.0,
    )

    assert anomaly is None
    assert result.rule_reference_code == "REF_CCNS_SENIORITY_G1_G6_2026"
    assert result.legal_certainty == LegalCertainty.MAJORITAIRE
    assert result.theoretical_value == 180.0
