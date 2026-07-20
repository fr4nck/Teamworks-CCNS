from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from domain.missions import Mission
from domain.people import Civility, Employee
from domain.qualifications import (
    EmployeeQualification,
    Qualification,
    QualificationCategory,
    QualificationEligibilityResult,
    QualificationEligibilityService,
    QualificationRequirement,
    QualificationStatus,
    RequirementLevel,
)


@pytest.fixture
def employee():
    return Employee(civility=Civility.MADAME, first_name="Ada", last_name="Lovelace")


@pytest.fixture
def other_employee():
    return Employee(civility=Civility.MONSIEUR, first_name="Alan", last_name="Turing")


def qualification(code="PSC1", name="Prévention et secours civiques", qualification_id=None):
    kwargs = {"id": qualification_id} if qualification_id is not None else {}
    return Qualification(
        code=code,
        name=name,
        category=QualificationCategory.CERTIFICATION,
        **kwargs,
    )


def requirement(qualification, level=RequirementLevel.REQUIRED, active=True):
    return QualificationRequirement(qualification=qualification, level=level, active=active)


def employee_qualification(employee, qualification, status=QualificationStatus.VALID, active=True):
    return EmployeeQualification(
        employee=employee,
        qualification=qualification,
        status=status,
        active=active,
    )


def evaluate(employee, requirements=(), employee_qualifications=()):
    mission = Mission(code="ALSH", name="Animation ALSH", qualification_requirements=requirements)
    return QualificationEligibilityService().evaluate(employee, mission, employee_qualifications)


def test_employee_is_eligible_without_required_requirement(employee):
    result = evaluate(employee)

    assert result.is_eligible()
    assert not result.has_missing_requirements()
    assert result.satisfied_count() == 0
    assert result.missing_count() == 0


def test_employee_is_eligible_when_all_required_requirements_are_satisfied(employee):
    psc1 = qualification()
    bafa = qualification("BAFA", "Brevet d'aptitude aux fonctions d'animateur")
    requirements = (requirement(psc1), requirement(bafa))

    result = evaluate(
        employee,
        requirements,
        (employee_qualification(employee, psc1), employee_qualification(employee, bafa)),
    )

    assert result.is_eligible()
    assert result.satisfied_requirements == requirements
    assert result.missing_requirements == ()


def test_employee_is_not_eligible_with_one_missing_requirement(employee):
    psc1 = qualification()
    bafa = qualification("BAFA", "Brevet d'aptitude aux fonctions d'animateur")
    psc1_requirement = requirement(psc1)
    bafa_requirement = requirement(bafa)

    result = evaluate(
        employee,
        (psc1_requirement, bafa_requirement),
        (employee_qualification(employee, psc1),),
    )

    assert not result.is_eligible()
    assert result.has_missing_requirements()
    assert result.satisfied_requirements == (psc1_requirement,)
    assert result.missing_requirements == (bafa_requirement,)


def test_employee_is_not_eligible_with_several_missing_requirements(employee):
    requirements = (
        requirement(qualification("PSC1", "Prévention et secours civiques")),
        requirement(qualification("BAFA", "Brevet d'aptitude aux fonctions d'animateur")),
    )

    result = evaluate(employee, requirements, ())

    assert not result.is_eligible()
    assert result.satisfied_count() == 0
    assert result.missing_count() == 2
    assert result.missing_requirements == requirements


@pytest.mark.parametrize("level", [RequirementLevel.RECOMMENDED, RequirementLevel.OPTIONAL])
def test_recommended_and_optional_requirements_are_ignored_for_eligibility(employee, level):
    result = evaluate(employee, (requirement(qualification(), level),), ())

    assert result.is_eligible()
    assert result.satisfied_requirements == ()
    assert result.missing_requirements == ()


def test_inactive_requirement_is_ignored(employee):
    result = evaluate(employee, (requirement(qualification(), active=False),), ())

    assert result.is_eligible()
    assert result.missing_requirements == ()


def test_valid_and_active_employee_qualification_is_recognized(employee):
    psc1 = qualification()
    psc1_requirement = requirement(psc1)

    result = evaluate(employee, (psc1_requirement,), (employee_qualification(employee, psc1),))

    assert result.satisfied_requirements == (psc1_requirement,)


@pytest.mark.parametrize(
    "status",
    [
        QualificationStatus.EXPIRED,
        QualificationStatus.SUSPENDED,
        QualificationStatus.PENDING,
        QualificationStatus.REVOKED,
    ],
)
def test_non_valid_statuses_are_ignored(employee, status):
    psc1 = qualification()
    psc1_requirement = requirement(psc1)

    result = evaluate(
        employee,
        (psc1_requirement,),
        (employee_qualification(employee, psc1, status=status),),
    )

    assert result.missing_requirements == (psc1_requirement,)


def test_inactive_employee_qualification_is_ignored(employee):
    psc1 = qualification()
    psc1_requirement = requirement(psc1)

    result = evaluate(
        employee,
        (psc1_requirement,),
        (employee_qualification(employee, psc1, active=False),),
    )

    assert result.missing_requirements == (psc1_requirement,)


def test_qualification_from_another_employee_is_ignored(employee, other_employee):
    psc1 = qualification()
    psc1_requirement = requirement(psc1)

    result = evaluate(
        employee,
        (psc1_requirement,),
        (employee_qualification(other_employee, psc1),),
    )

    assert result.missing_requirements == (psc1_requirement,)


def test_comparison_uses_qualification_identity_not_name(employee):
    shared_name = "Prévention et secours civiques"
    required = qualification("PSC1", shared_name, uuid4())
    held = qualification("PSC1-BIS", shared_name, uuid4())
    psc1_requirement = requirement(required)

    result = evaluate(
        employee,
        (psc1_requirement,),
        (employee_qualification(employee, held),),
    )

    assert result.missing_requirements == (psc1_requirement,)


def test_requirement_order_is_preserved(employee):
    psc1 = qualification("PSC1", "Prévention et secours civiques")
    bafa = qualification("BAFA", "Brevet d'aptitude aux fonctions d'animateur")
    bpjeps = qualification("BPJEPS", "Brevet professionnel jeunesse")
    requirements = (requirement(psc1), requirement(bafa), requirement(bpjeps))

    result = evaluate(employee, requirements, (employee_qualification(employee, bafa),))

    assert result.satisfied_requirements == (requirements[1],)
    assert result.missing_requirements == (requirements[0], requirements[2])


def test_result_collections_are_tuples(employee):
    result = QualificationEligibilityResult(
        employee=employee,
        mission=Mission(code="ALSH", name="Animation ALSH"),
        satisfied_requirements=[],
        missing_requirements=[],
    )

    assert isinstance(result.satisfied_requirements, tuple)
    assert isinstance(result.missing_requirements, tuple)


def test_result_is_immutable(employee):
    result = evaluate(employee)

    with pytest.raises(FrozenInstanceError):
        result.missing_requirements = ()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"employee": object()}, "Employee"),
        ({"mission": object()}, "Mission"),
        ({"employee_qualifications": object()}, "collection"),
        ({"employee_qualifications": (object(),)}, "EmployeeQualification"),
    ],
)
def test_service_rejects_invalid_arguments(employee, kwargs, message):
    data = {
        "employee": employee,
        "mission": Mission(code="ALSH", name="Animation ALSH"),
        "employee_qualifications": (),
    }
    data.update(kwargs)

    with pytest.raises(ValueError, match=message):
        QualificationEligibilityService().evaluate(**data)


def test_service_accepts_empty_collection(employee):
    result = QualificationEligibilityService().evaluate(
        employee,
        Mission(code="ALSH", name="Animation ALSH"),
        [],
    )

    assert result.is_eligible()
