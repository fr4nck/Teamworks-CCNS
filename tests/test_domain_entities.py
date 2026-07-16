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


def test_contract_accepts_signature_date_after_start_date():
    contract = Contract(
        person_id="person-1",
        contract_type=ContractType.CDI,
        start_date=date(2026, 9, 1),
        signature_date=date(2026, 9, 15),
    )

    assert contract.signature_date == date(2026, 9, 15)


def test_contract_signature_date_is_optional_and_must_be_a_date():
    contract = Contract(person_id="person-1", contract_type=ContractType.CDI)
    assert contract.signature_date is None

    with pytest.raises(ValueError, match="signature_date must be a date"):
        Contract(
            person_id="person-1",
            contract_type=ContractType.CDI,
            signature_date="2026-09-01",  # type: ignore[arg-type]
        )


def test_cdii_can_be_created_without_end_date():
    contract = Contract(person_id="person-1", contract_type=ContractType.CDII)

    assert contract.is_open_ended is True


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
def test_fixed_term_contract_types_require_an_end_date(contract_type):
    with pytest.raises(ValueError, match="end_date is required"):
        Contract(person_id="person-1", contract_type=contract_type)
