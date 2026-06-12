from datetime import date

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
