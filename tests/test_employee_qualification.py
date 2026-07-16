from dataclasses import FrozenInstanceError
from datetime import date
from uuid import uuid4

import pytest

from domain.people import Civility, Employee
from domain.qualifications import (
    EmployeeQualification,
    Qualification,
    QualificationCategory,
    QualificationStatus,
)


@pytest.fixture
def employee():
    return Employee(civility=Civility.MADAME, first_name="Ada", last_name="Lovelace")


@pytest.fixture
def qualification():
    return Qualification(
        code="PSC1",
        name="Prévention et secours civiques de niveau 1",
        category=QualificationCategory.CERTIFICATION,
    )


def test_employee_qualification_is_created_with_normalized_optional_data(employee, qualification):
    qualification_id = uuid4()

    employee_qualification = EmployeeQualification(
        id=qualification_id,
        employee=employee,
        qualification=qualification,
        status=QualificationStatus.VALID,
        obtained_at=date(2024, 1, 1),
        expires_at=date(2027, 1, 1),
        issuing_organization="  Croix-Rouge française  ",
        certificate_number="  PSC1-123  ",
        observations="  Original vérifié.  ",
    )

    assert employee_qualification.id == qualification_id
    assert employee_qualification.employee is employee
    assert employee_qualification.qualification is qualification
    assert employee_qualification.issuing_organization == "Croix-Rouge française"
    assert employee_qualification.certificate_number == "PSC1-123"
    assert employee_qualification.observations == "Original vérifié."
    assert employee_qualification.active is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"employee": None}, "salarié"),
        ({"qualification": None}, "qualification"),
        ({"status": "VALID"}, "statut"),
        ({"obtained_at": "2024-01-01"}, "obtention"),
        ({"expires_at": "2027-01-01"}, "expiration"),
        ({"obtained_at": date(2027, 1, 2), "expires_at": date(2027, 1, 1)}, "antérieure"),
        ({"issuing_organization": " "}, "organisme délivrant"),
        ({"certificate_number": 12}, "numéro de certificat"),
        ({"observations": []}, "observations"),
        ({"active": 1}, "booléen"),
    ],
)
def test_employee_qualification_rejects_invalid_data(employee, qualification, kwargs, message):
    data = {
        "employee": employee,
        "qualification": qualification,
        "status": QualificationStatus.VALID,
    }
    data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        EmployeeQualification(**data)


def test_valid_qualification_is_valid_without_date_calculation(employee, qualification):
    employee_qualification = EmployeeQualification(
        employee=employee,
        qualification=qualification,
        status=QualificationStatus.VALID,
        expires_at=date(2000, 1, 1),
    )

    assert employee_qualification.is_valid()
    assert not employee_qualification.is_expired()


def test_expired_qualification_is_expired(employee, qualification):
    employee_qualification = EmployeeQualification(
        employee=employee,
        qualification=qualification,
        status=QualificationStatus.EXPIRED,
    )

    assert employee_qualification.is_expired()
    assert not employee_qualification.is_valid()


def test_suspended_qualification_is_neither_valid_nor_expired(employee, qualification):
    employee_qualification = EmployeeQualification(
        employee=employee,
        qualification=qualification,
        status=QualificationStatus.SUSPENDED,
    )

    assert not employee_qualification.is_valid()
    assert not employee_qualification.is_expired()


def test_qualification_without_expiration_has_no_expiration(employee, qualification):
    employee_qualification = EmployeeQualification(
        employee=employee,
        qualification=qualification,
        status=QualificationStatus.PENDING,
    )

    assert not employee_qualification.has_expiration()


def test_employee_qualification_is_immutable(employee, qualification):
    employee_qualification = EmployeeQualification(
        employee=employee,
        qualification=qualification,
        status=QualificationStatus.VALID,
    )

    with pytest.raises(FrozenInstanceError):
        employee_qualification.active = False
