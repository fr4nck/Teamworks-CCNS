from dataclasses import FrozenInstanceError
from datetime import date
from uuid import uuid4

import pytest

from domain.people import Civility, Contract, ContractStatus, ContractType, Employee


def _employee(*, active=True):
    return Employee(
        civility=Civility.MADAME,
        first_name="Ada",
        last_name="Lovelace",
        active=active,
    )


def _contract(**kwargs):
    values = {
        "employee": _employee(),
        "contract_type": ContractType.CDI,
        "start_date": date(2026, 1, 1),
        "status": ContractStatus.ACTIVE,
    }
    values.update(kwargs)
    return Contract(**values)


def test_cdi_can_be_created_without_an_end_date():
    assert _contract().end_date is None


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
def test_fixed_term_contracts_require_an_end_date(contract_type):
    with pytest.raises(ValueError, match="date de fin"):
        _contract(contract_type=contract_type)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"end_date": date(2025, 12, 31)}, "date de fin"),
        ({"signature_date": date(2026, 1, 2)}, "signature"),
        ({"probation_end_date": date(2025, 12, 31)}, "période d'essai"),
        (
            {"end_date": date(2026, 1, 10), "probation_end_date": date(2026, 1, 11)},
            "période d'essai",
        ),
    ],
)
def test_contract_rejects_incoherent_dates(kwargs, message):
    with pytest.raises(ValueError, match=message):
        _contract(**kwargs)


def test_active_contract_is_effective_only_during_its_period():
    contract = _contract(end_date=date(2026, 1, 31))

    assert contract.is_effective(date(2026, 1, 1)) is True
    assert contract.is_effective(date(2026, 1, 31)) is True
    assert contract.is_effective(date(2025, 12, 31)) is False
    assert contract.is_effective(date(2026, 2, 1)) is False


@pytest.mark.parametrize("status", [ContractStatus.DRAFT, ContractStatus.ENDED, ContractStatus.CANCELLED])
def test_non_active_contract_is_never_effective(status):
    assert _contract(status=status).is_effective(date(2026, 1, 1)) is False


def test_contract_is_immutable_and_normalizes_internal_reference():
    contract = _contract(internal_reference=" REF-42 ")

    assert contract.internal_reference == "REF-42"
    with pytest.raises(FrozenInstanceError):
        contract.status = ContractStatus.ENDED


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "invalid"}, "UUID"),
        ({"employee": "Ada"}, "Employee"),
        ({"contract_type": "CDI"}, "type de contrat"),
        ({"status": "ACTIVE"}, "statut"),
        ({"start_date": "2026-01-01"}, "date"),
        ({"end_date": "2026-01-02"}, "date"),
        ({"internal_reference": " "}, "référence"),
    ],
)
def test_contract_rejects_invalid_types(kwargs, message):
    with pytest.raises(ValueError, match=message):
        _contract(**kwargs)


def test_inactive_employee_can_keep_a_contract():
    contract = _contract(employee=_employee(active=False), id=uuid4())

    assert contract.employee.active is False
