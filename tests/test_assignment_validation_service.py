from dataclasses import FrozenInstanceError
from datetime import datetime, time
from uuid import uuid4

import pytest

from domain.missions import Mission, MissionOccurrence, MissionOccurrenceAssignment, MissionOccurrenceAssignmentStatus
from domain.people import Civility, Employee
from domain.planning import (
    AssignmentValidationIssue,
    AssignmentValidationIssueType,
    AssignmentValidationResult,
    AssignmentValidationService,
    EmployeeUnavailability,
    EmployeeUnavailabilityReason,
    EmployeeWeeklyAvailability,
    PlanningConflictService,
    UnavailabilityConflictService,
    Weekday,
    WeeklyAvailabilityService,
)
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


def employee(name="Ada"):
    return Employee(civility=Civility.MADAME, first_name=name, last_name="Lovelace")


def qualification(code="BAFA"):
    return Qualification(code=code, name=code, category=QualificationCategory.CERTIFICATION)


def requirement(qual=None):
    return QualificationRequirement(qualification=qual or qualification(), level=RequirementLevel.REQUIRED)


def assignment(emp=None, start=datetime(2026, 7, 20, 9), end=datetime(2026, 7, 20, 17), reqs=()):
    emp = emp or employee()
    mission = Mission(code="ALSH", name="Animation", qualification_requirements=reqs)
    occurrence = MissionOccurrence(mission=mission, starts_at=start, ends_at=end)
    return MissionOccurrenceAssignment(employee=emp, occurrence=occurrence, status=MissionOccurrenceAssignmentStatus.PLANNED)


def availability(emp, start=time(9), end=time(17)):
    return EmployeeWeeklyAvailability(employee=emp, weekday=Weekday.MONDAY, starts_at=start, ends_at=end)


def unavailability(emp, start=datetime(2026, 7, 20, 10), end=datetime(2026, 7, 20, 12)):
    return EmployeeUnavailability(employee=emp, starts_at=start, ends_at=end, reason=EmployeeUnavailabilityReason.PERSONAL)


def service():
    return AssignmentValidationService(
        QualificationEligibilityService(),
        PlanningConflictService(),
        UnavailabilityConflictService(),
        WeeklyAvailabilityService(),
    )


def test_affectation_entierement_valide():
    emp = employee()
    req = requirement()
    assign = assignment(emp, reqs=(req,))

    result = service().validate(assign, (req,), (EmployeeQualification(emp, req.qualification, QualificationStatus.VALID),), (), (), (availability(emp),))

    assert result.is_valid() is True
    assert result.has_issues() is False
    assert result.issues == ()


def test_probleme_de_qualification_uniquement_et_detail_origine():
    emp = employee(); req = requirement(); assign = assignment(emp)
    result = service().validate(assign, [req], [], [], [], [availability(emp)])

    assert result.valid is False
    assert result.issue_count() == 1
    issue = result.issues[0]
    assert issue.is_qualification_issue() is True
    assert isinstance(issue.detail, QualificationEligibilityResult)
    assert issue.detail.missing_requirements == (req,)


def test_conflit_de_planning_uniquement_et_plusieurs_conflits():
    emp = employee(); assign = assignment(emp)
    conflicts = [assignment(emp, datetime(2026, 7, 20, 8), datetime(2026, 7, 20, 10)), assignment(emp, datetime(2026, 7, 20, 16), datetime(2026, 7, 20, 18))]

    result = service().validate(assign, (), (), conflicts, (), (availability(emp),))

    assert [issue.issue_type for issue in result.issues] == [AssignmentValidationIssueType.PLANNING_CONFLICT] * 2
    assert result.issues[0].detail is not result.issues[1].detail


def test_conflit_indisponibilite_uniquement_et_plusieurs_conflits():
    emp = employee(); assign = assignment(emp)
    result = service().validate(assign, (), (), (), (unavailability(emp), unavailability(emp, datetime(2026, 7, 20, 13), datetime(2026, 7, 20, 14))), (availability(emp),))

    assert result.issue_count() == 2
    assert all(issue.is_unavailability_issue() for issue in result.issues)


def test_absence_de_disponibilite_hebdomadaire_uniquement():
    emp = employee(); assign = assignment(emp)
    result = service().validate(assign, (), (), (), (), ())

    assert result.issue_count() == 1
    assert result.issues[0].is_weekly_availability_issue() is True


def test_quatre_categories_executees_et_ordonnees():
    emp = employee(); req = requirement(); assign = assignment(emp)
    result = service().validate(assign, (req,), (), (assignment(emp, datetime(2026, 7, 20, 8), datetime(2026, 7, 20, 10)),), (unavailability(emp),), ())

    assert [issue.issue_type for issue in result.issues] == [
        AssignmentValidationIssueType.QUALIFICATION,
        AssignmentValidationIssueType.PLANNING_CONFLICT,
        AssignmentValidationIssueType.UNAVAILABILITY,
        AssignmentValidationIssueType.WEEKLY_AVAILABILITY,
    ]


def test_absence_de_doublons_exacts_et_conservation_des_distincts():
    emp = employee(); assign = assignment(emp); same = assignment(emp, datetime(2026, 7, 20, 8), datetime(2026, 7, 20, 10))
    other = assignment(emp, datetime(2026, 7, 20, 11), datetime(2026, 7, 20, 12))
    result = service().validate(assign, (), (), (same, same, other), (), (availability(emp),))

    assert result.issue_count() == 2
    assert result.has_issue_type(AssignmentValidationIssueType.PLANNING_CONFLICT) is True
    assert len(result.issues_of_type(AssignmentValidationIssueType.PLANNING_CONFLICT)) == 2


def test_validation_stricte_resultat_issue_uuid_booleens_et_immutabilite():
    emp = employee(); assign = assignment(emp); qresult = QualificationEligibilityResult(emp, assign.occurrence.mission, (), (requirement(),))
    issue = AssignmentValidationIssue(AssignmentValidationIssueType.QUALIFICATION, qresult, id=uuid4())
    assert AssignmentValidationResult(assign, False, (issue,)).has_issues() is True
    with pytest.raises(ValueError, match="booléen"):
        AssignmentValidationResult(assign, 1, ())
    with pytest.raises(ValueError, match="tuple"):
        AssignmentValidationResult(assign, False, [issue])
    with pytest.raises(ValueError, match="UUID"):
        AssignmentValidationIssue(AssignmentValidationIssueType.QUALIFICATION, qresult, id="bad")
    with pytest.raises(ValueError, match="correspond"):
        AssignmentValidationIssue(AssignmentValidationIssueType.PLANNING_CONFLICT, qresult)
    with pytest.raises(FrozenInstanceError):
        issue.detail = object()


def test_collections_invalides_chaines_elements_invalides_et_generateurs():
    emp = employee(); assign = assignment(emp)
    with pytest.raises(ValueError, match="iterable"):
        service().validate(assign, "bad", (), (), (), ())
    with pytest.raises(ValueError, match="iterable"):
        service().validate(assign, (), b"bad", (), (), ())
    with pytest.raises(ValueError, match="QualificationRequirement"):
        service().validate(assign, [object()], (), (), (), ())
    consumed = 0
    def gen():
        nonlocal consumed
        consumed += 1
        yield availability(emp)
    assert service().validate(assign, (), (), (), (), gen()).is_valid() is True
    assert consumed == 1


def test_validation_stricte_services_et_assignment():
    with pytest.raises(ValueError, match="qualification"):
        AssignmentValidationService(object(), PlanningConflictService(), UnavailabilityConflictService(), WeeklyAvailabilityService())
    with pytest.raises(ValueError, match="affectation"):
        service().validate(object(), (), (), (), (), ())


def test_tous_les_services_sont_executes_meme_apres_premier_probleme():
    calls = []

    class QualificationSpy(QualificationEligibilityService):
        def evaluate(self, *args, **kwargs):
            calls.append("qualification")
            return super().evaluate(*args, **kwargs)

    class PlanningSpy(PlanningConflictService):
        def evaluate(self, *args, **kwargs):
            calls.append("planning")
            return super().evaluate(*args, **kwargs)

    class UnavailabilitySpy(UnavailabilityConflictService):
        def evaluate(self, *args, **kwargs):
            calls.append("unavailability")
            return super().evaluate(*args, **kwargs)

    class WeeklySpy(WeeklyAvailabilityService):
        def check(self, *args, **kwargs):
            calls.append("weekly")
            return super().check(*args, **kwargs)

    emp = employee()
    req = requirement()
    assign = assignment(emp)
    validator = AssignmentValidationService(
        QualificationSpy(),
        PlanningSpy(),
        UnavailabilitySpy(),
        WeeklySpy(),
    )

    result = validator.validate(assign, (req,), (), (), (), ())

    assert result.valid is False
    assert calls == ["qualification", "planning", "unavailability", "weekly"]
