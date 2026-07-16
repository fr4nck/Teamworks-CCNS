from datetime import date

import pytest

from domain.people.person import Person
from domain.people.legal_profile import LegalProfile, AgeGroup
from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.contracts.employment_regime import EmploymentRegime
from domain.contracts.time_organization import TimeOrganization


def test_person_display_name_falls_back_to_names():
    person = Person(code_internal="P001", first_name="Jean", last_name="Dupont")
    assert person.display_name == "Jean Dupont"


def test_legal_profile_requires_person_id():
    try:
        LegalProfile()
    except ValueError:
        assert True
    else:
        assert False


def test_contract_basic_creation():
    contract = Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        employment_regime=EmploymentRegime.CCNS_STANDARD,
        time_organization=TimeOrganization.WEEKLY_CONSTANT,
        start_date=date(2026, 9, 1),
        weekly_reference_hours=35,
        base_salary_amount=2000.0,
        salary_unit="monthly",
    )
    assert contract.is_ccns is True


def test_employment_regimes_do_not_duplicate_historical_business_regimes():
    """Les codes d'import ne créent pas de nouveaux régimes métier."""
    assert EmploymentRegime.__members__.keys() >= {
        "APPRENTICE",
        "SERVICE_CIVIQUE",
        "STAGE_PFMP",
    }
    assert not EmploymentRegime.__members__.keys() & {
        "APPRENTICESHIP",
        "CIVIC_SERVICE",
        "INTERNSHIP",
    }


@pytest.mark.parametrize(
    "contract_type",
    [
        ContractType.CDD,
        ContractType.CEE,
        ContractType.APPRENTICESHIP,
        ContractType.INTERNSHIP,
        ContractType.CIVIC_SERVICE,
    ],
)
def test_fixed_term_contract_requires_end_date(contract_type):
    with pytest.raises(ValueError, match="end_date is required for fixed-term contracts"):
        Contract(person_id="person-1", contract_type=contract_type)
