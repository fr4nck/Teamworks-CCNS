from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from domain.qualifications import (
    Qualification,
    QualificationCategory,
    QualificationRequirement,
    RequirementLevel,
)


@pytest.fixture
def qualification():
    return Qualification(
        code="PSC1",
        name="Prévention et secours civiques de niveau 1",
        category=QualificationCategory.CERTIFICATION,
    )


def test_qualification_requirement_is_created_with_normalized_observations(qualification):
    requirement_id = uuid4()

    requirement = QualificationRequirement(
        id=requirement_id,
        qualification=qualification,
        level=RequirementLevel.REQUIRED,
        mandatory=True,
        observations="  Requis pour les sorties avec nuitée.  ",
    )

    assert requirement.id == requirement_id
    assert requirement.qualification is qualification
    assert requirement.level is RequirementLevel.REQUIRED
    assert requirement.mandatory is True
    assert requirement.active is True
    assert requirement.observations == "Requis pour les sorties avec nuitée."


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"qualification": None}, "qualification"),
        ({"qualification": "PSC1"}, "qualification"),
        ({"level": "required"}, "niveau d'exigence"),
        ({"mandatory": 1}, "booléen"),
        ({"active": None}, "booléen"),
        ({"observations": " "}, "observations"),
        ({"observations": []}, "observations"),
    ],
)
def test_qualification_requirement_rejects_invalid_data(qualification, kwargs, message):
    data = {
        "qualification": qualification,
        "level": RequirementLevel.REQUIRED,
    }
    data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        QualificationRequirement(**data)


@pytest.mark.parametrize(
    ("level", "method_name"),
    [
        (RequirementLevel.REQUIRED, "is_required"),
        (RequirementLevel.RECOMMENDED, "is_recommended"),
        (RequirementLevel.OPTIONAL, "is_optional"),
    ],
)
def test_qualification_requirement_identifies_its_level(qualification, level, method_name):
    requirement = QualificationRequirement(qualification=qualification, level=level)

    assert getattr(requirement, method_name)()
    assert sum(
        (
            requirement.is_required(),
            requirement.is_recommended(),
            requirement.is_optional(),
        )
    ) == 1


def test_qualification_requirement_is_immutable(qualification):
    requirement = QualificationRequirement(
        qualification=qualification,
        level=RequirementLevel.OPTIONAL,
    )

    with pytest.raises(FrozenInstanceError):
        requirement.active = False
