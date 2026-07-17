from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from domain.missions import Mission
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


@pytest.fixture
def requirements(qualification):
    return (
        QualificationRequirement(qualification, RequirementLevel.REQUIRED, mandatory=False),
        QualificationRequirement(qualification, RequirementLevel.RECOMMENDED),
        QualificationRequirement(qualification, RequirementLevel.OPTIONAL),
    )


def test_mission_is_created_without_qualification_requirement():
    mission = Mission(code="animation-alsh", name="Animation ALSH")

    assert mission.qualification_requirements == ()
    assert not mission.has_qualification_requirements()
    assert mission.qualification_requirement_count() == 0


def test_mission_is_created_with_multiple_qualification_requirements(requirements):
    mission = Mission(
        code="direction-alsh",
        name="Direction ALSH",
        qualification_requirements=requirements,
    )

    assert mission.qualification_requirements == requirements
    assert mission.has_qualification_requirements()
    assert mission.qualification_requirement_count() == 3


def test_mission_generates_an_identifier_automatically():
    assert isinstance(Mission(code="ALSH", name="Animation ALSH").id, type(uuid4()))


def test_mission_accepts_an_explicit_uuid():
    mission_id = uuid4()

    assert Mission(id=mission_id, code="ALSH", name="Animation ALSH").id == mission_id


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"id": "not-a-uuid"}, "UUID"),
        ({"code": " "}, "code"),
        ({"code": 42}, "code"),
        ({"name": " "}, "nom"),
        ({"description": " "}, "description"),
        ({"active": 1}, "booléen"),
        ({"qualification_requirements": None}, "collection"),
        ({"qualification_requirements": ("invalid",)}, "QualificationRequirement"),
    ],
)
def test_mission_rejects_invalid_data(kwargs, message):
    data = {"code": "ALSH", "name": "Animation ALSH"}
    data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        Mission(**data)


def test_mission_normalizes_its_text_fields():
    mission = Mission(
        code="  animation-alsh  ",
        name="  Animation ALSH  ",
        description="  Anime les accueils de loisirs.  ",
    )

    assert mission.code == "ANIMATION-ALSH"
    assert mission.name == "Animation ALSH"
    assert mission.description == "Anime les accueils de loisirs."


def test_mission_rejects_duplicate_qualification_requirement_identifiers(qualification):
    requirement_id = uuid4()
    first = QualificationRequirement(
        id=requirement_id,
        qualification=qualification,
        level=RequirementLevel.REQUIRED,
    )
    second = QualificationRequirement(
        id=requirement_id,
        qualification=qualification,
        level=RequirementLevel.OPTIONAL,
    )

    with pytest.raises(ValueError, match="même identifiant"):
        Mission(code="ALSH", name="Animation ALSH", qualification_requirements=(first, second))


def test_mission_converts_requirements_to_an_immutable_tuple(requirements):
    mission = Mission(
        code="ALSH",
        name="Animation ALSH",
        qualification_requirements=list(requirements),
    )

    assert mission.qualification_requirements == requirements
    assert isinstance(mission.qualification_requirements, tuple)

    with pytest.raises(FrozenInstanceError):
        mission.active = False


def test_mission_filters_requirements_from_their_requirement_level(requirements):
    mission = Mission(
        code="ALSH",
        name="Animation ALSH",
        qualification_requirements=requirements,
    )

    required = mission.required_qualification_requirements()
    recommended = mission.recommended_qualification_requirements()
    optional = mission.optional_qualification_requirements()

    assert required == (requirements[0],)
    assert recommended == (requirements[1],)
    assert optional == (requirements[2],)
    assert all(isinstance(result, tuple) for result in (required, recommended, optional))
