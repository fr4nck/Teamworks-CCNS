from dataclasses import FrozenInstanceError
from datetime import date, timedelta
from uuid import uuid4

import pytest

from domain.people.civility import Civility
from domain.people.employee import Employee


def test_employee_carries_only_normalized_identity_data():
    employee_id = uuid4()
    employee = Employee(
        id=employee_id,
        civility=Civility.MONSIEUR,
        first_name=" Ada ",
        last_name=" Lovelace ",
        birth_date=date(1815, 12, 10),
        professional_email=" ADA@EXAMPLE.ORG ",
        professional_phone=" +33 2 43 00 00 00 ",
    )

    assert employee.id == employee_id
    assert employee.civility is Civility.MONSIEUR
    assert employee.first_name == "Ada"
    assert employee.last_name == "Lovelace"
    assert employee.birth_date == date(1815, 12, 10)
    assert employee.professional_email == "ada@example.org"
    assert employee.professional_phone == "+33 2 43 00 00 00"
    assert employee.active is True


def test_employee_allows_absent_optional_identity_data():
    employee = Employee(civility=Civility.MADAME, first_name="Grace", last_name="Hopper")

    assert employee.birth_date is None
    assert employee.professional_email is None
    assert employee.professional_phone is None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"civility": "monsieur"}, "civilité"),
        ({"first_name": " "}, "prénom"),
        ({"last_name": " "}, "nom"),
        ({"birth_date": date.today() + timedelta(days=1)}, "future"),
        ({"professional_email": "not-an-email"}, "email professionnel"),
        ({"professional_phone": " "}, "téléphone professionnel"),
        ({"active": "yes"}, "booléen"),
    ],
)
def test_employee_rejects_invalid_identity_data(kwargs, message):
    employee_data = {
        "civility": Civility.MADAME,
        "first_name": "Ada",
        "last_name": "Lovelace",
    }
    employee_data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        Employee(**employee_data)


def test_employee_is_immutable():
    employee = Employee(civility=Civility.MADAME, first_name="Ada", last_name="Lovelace")

    with pytest.raises(FrozenInstanceError):
        employee.active = False
