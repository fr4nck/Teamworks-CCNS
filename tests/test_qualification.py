from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from domain.qualifications import Qualification, QualificationCategory


def test_qualification_is_created_with_normalized_required_data():
    qualification_id = uuid4()

    qualification = Qualification(
        id=qualification_id,
        code="  PSC1  ",
        name="  Prévention et secours civiques de niveau 1  ",
        category=QualificationCategory.CERTIFICATION,
        mandatory=True,
    )

    assert qualification.id == qualification_id
    assert qualification.code == "PSC1"
    assert qualification.name == "Prévention et secours civiques de niveau 1"
    assert qualification.category is QualificationCategory.CERTIFICATION
    assert qualification.mandatory is True
    assert qualification.active is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"code": " "}, "code"),
        ({"code": 12}, "code"),
        ({"name": " "}, "nom"),
        ({"name": 12}, "nom"),
        ({"category": "CERTIFICATION"}, "catégorie"),
        ({"validity_duration_days": -1}, "négative"),
        ({"validity_duration_days": 1.5}, "entier"),
        ({"validity_duration_days": True}, "entier"),
        ({"renewable": "yes"}, "booléen"),
        ({"mandatory": 1}, "booléen"),
        ({"active": None}, "booléen"),
    ],
)
def test_qualification_rejects_invalid_data(kwargs, message):
    qualification_data = {
        "code": "PSC1",
        "name": "Prévention et secours civiques de niveau 1",
        "category": QualificationCategory.CERTIFICATION,
    }
    qualification_data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        Qualification(**qualification_data)


def test_permanent_qualification_has_neither_expiration_nor_required_renewal():
    qualification = Qualification(
        code="DEJEPS",
        name="Diplôme d'État de la jeunesse, de l'éducation populaire et du sport",
        category=QualificationCategory.DIPLOMA,
    )

    assert qualification.is_permanent()
    assert not qualification.has_expiration()
    assert not qualification.requires_renewal()


def test_renewable_qualification_requires_renewal():
    qualification = Qualification(
        code="HAB-ELEC",
        name="Habilitation électrique",
        category=QualificationCategory.AUTHORIZATION,
        validity_duration_days=1095,
        renewable=True,
    )

    assert qualification.requires_renewal()


def test_qualification_with_validity_duration_has_expiration():
    qualification = Qualification(
        code="PERMIS-B",
        name="Permis de conduire B",
        category=QualificationCategory.LICENSE,
        validity_duration_days=3650,
    )

    assert qualification.has_expiration()
    assert not qualification.is_permanent()


def test_qualification_is_immutable():
    qualification = Qualification(
        code="BAFA",
        name="Brevet d'aptitude aux fonctions d'animateur",
        category=QualificationCategory.TRAINING,
    )

    with pytest.raises(FrozenInstanceError):
        qualification.active = False
