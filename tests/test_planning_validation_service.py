from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, time

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
    Planning,
    PlanningConflictService,
    PlanningValidationResult,
    PlanningValidationService,
    PlanningStatus,
    PlanningStatusTransitionFailureReason,
    PlanningStatusTransitionService,
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


def assignment_service():
    return AssignmentValidationService(
        QualificationEligibilityService(),
        PlanningConflictService(),
        UnavailabilityConflictService(),
        WeeklyAvailabilityService(),
    )


def planning_service(service=None):
    return PlanningValidationService(service or assignment_service())


def invalid_result(assign):
    qresult = QualificationEligibilityResult(assign.employee, assign.occurrence.mission, (), (requirement(),))
    issue = AssignmentValidationIssue(AssignmentValidationIssueType.QUALIFICATION, qresult)
    return AssignmentValidationResult(assign, False, (issue,))


def test_planning_entierement_valide_listes_tuples_et_result_for():
    emp = employee(); req = requirement(); a = assignment(emp, reqs=(req,))
    result = planning_service().validate([a], (req,), [EmployeeQualification(emp, req.qualification, QualificationStatus.VALID)], [], [availability(emp)])

    assert result.is_valid() is True
    assert result.has_invalid_assignments() is False
    assert result.assignment_count() == 1
    assert result.valid_assignment_count() == 1
    assert result.invalid_assignment_count() == 0
    assert result.valid_results() == result.assignment_results
    assert result.invalid_results() == ()
    assert result.result_for(a) is result.assignment_results[0]


def test_planning_avec_une_et_plusieurs_affectations_invalides_et_tous_les_resultats():
    emp = employee(); other = employee("Grace")
    a = assignment(emp); b = assignment(other); c = assignment(employee("Hedy"))

    result = planning_service().validate((a, b, c), (), (), (unavailability(emp),), (availability(emp), availability(other)))

    assert result.valid is False
    assert result.assignment_results[0].is_valid() is False
    assert result.assignment_results[1].is_valid() is True
    assert result.assignment_results[2].is_valid() is False
    assert result.assignment_count() == 3
    assert result.valid_assignment_count() == 1
    assert result.invalid_assignment_count() == 2
    assert result.invalid_results() == (result.assignment_results[0], result.assignment_results[2])


def test_ordre_absence_arret_anticipe_appel_unique_et_existing_assignments():
    calls = []

    class Spy(AssignmentValidationService):
        def __init__(self):
            pass

        def validate(self, assignment, qualification_requirements, employee_qualifications, existing_assignments, unavailabilities, weekly_availabilities):
            calls.append((assignment, existing_assignments))
            return invalid_result(assignment)

    a = assignment(employee("A")); b = assignment(employee("B")); c = assignment(employee("C"))
    result = planning_service(Spy()).validate((a, b, c), (), (), (), ())

    assert [r.assignment for r in result.assignment_results] == [a, b, c]
    assert [call[0] for call in calls] == [a, b, c]
    assert calls[0][1] == (b, c)
    assert calls[1][1] == (a, c)
    assert calls[2][1] == (a, b)
    assert all(call[0] not in call[1] for call in calls)


def test_conflits_croises_entre_deux_affectations():
    emp = employee(); a = assignment(emp); b = assignment(emp, datetime(2026, 7, 20, 10), datetime(2026, 7, 20, 12))
    result = planning_service().validate((a, b), (), (), (), (availability(emp),))

    assert result.valid is False
    assert all(r.has_issue_type(AssignmentValidationIssueType.PLANNING_CONFLICT) for r in result.assignment_results)


def test_collections_invalides_doublons_et_elements_invalides():
    emp = employee(); a = assignment(emp); duplicate = replace(a)
    for bad in ((), "bad", b"bad", 42):
        with pytest.raises(ValueError):
            planning_service().validate(bad, (), (), (), ())
    with pytest.raises(ValueError, match="identifiant métier"):
        planning_service().validate((a, duplicate), (), (), (), ())
    with pytest.raises(ValueError, match="MissionOccurrenceAssignment"):
        planning_service().validate((object(),), (), (), (), ())

    invalids = [([object()], (), (), ()), ((), [object()], (), ()), ((), (), [object()], ()), ((), (), (), [object()])]
    for requirements, qualifications, unavailabilities, weekly in invalids:
        with pytest.raises(ValueError):
            planning_service().validate((a,), requirements, qualifications, unavailabilities, weekly)


def test_generateurs_acceptes_et_materialises_une_seule_fois():
    emp = employee(); a = assignment(emp)
    consumed = {"assignments": 0, "weekly": 0}

    def assignments_gen():
        consumed["assignments"] += 1
        yield a

    def weekly_gen():
        consumed["weekly"] += 1
        yield availability(emp)

    result = planning_service().validate(assignments_gen(), (), (), (), weekly_gen())

    assert result.valid is True
    assert consumed == {"assignments": 1, "weekly": 1}


def test_coherence_stricte_resultat_booleens_immutabilite_et_absence():
    a = assignment(); ok = AssignmentValidationResult(a, True, ())
    ko = invalid_result(assignment(employee("Grace")))

    assert PlanningValidationResult((ok,), True).valid is True
    with pytest.raises(ValueError, match="cohérente"):
        PlanningValidationResult((ko,), True)
    with pytest.raises(ValueError, match="cohérente"):
        PlanningValidationResult((ok,), False)
    with pytest.raises(ValueError, match="booléen"):
        PlanningValidationResult((ok,), 1)
    with pytest.raises(ValueError, match="tuple"):
        PlanningValidationResult([ok], True)
    with pytest.raises(ValueError, match="présente"):
        PlanningValidationResult((ok,), True).result_for(assignment(employee("Absent")))
    with pytest.raises(ValueError, match="MissionOccurrenceAssignment"):
        PlanningValidationResult((ok,), True).result_for(object())
    with pytest.raises(FrozenInstanceError):
        PlanningValidationResult((ok,), True).valid = False


def test_validation_stricte_service_injecte():
    with pytest.raises(ValueError, match="validation d'affectation"):
        PlanningValidationService(object())


def planning(*assignments_, status=PlanningStatus.DRAFT, active=True):
    return Planning(
        code="ETE-2026",
        name="Planning été",
        starts_on=date(2026, 7, 1),
        ends_on=date(2026, 7, 31),
        assignments=assignments_,
        status=status,
        active=active,
    )


def test_validate_planning_direct_valide_une_et_plusieurs_affectations_ordre_uuid_et_contenu():
    emp = employee("Ada"); other = employee("Grace")
    req = requirement()
    a = assignment(emp, reqs=(req,))
    b = assignment(other, reqs=(req,))
    p = planning(a, b)
    emp_qualification = EmployeeQualification(emp, req.qualification, QualificationStatus.VALID)
    other_qualification = EmployeeQualification(other, req.qualification, QualificationStatus.VALID)

    result = planning_service().validate_planning(
        p,
        [req],
        [emp_qualification, other_qualification],
        [],
        [availability(emp), availability(other)],
    )

    assert result.is_valid() is True
    assert result.assignment_count() == 2
    assert [item.assignment for item in result.assignment_results] == [a, b]
    assert [item.assignment.id for item in result.assignment_results] == [a.id, b.id]
    assert tuple(item.assignment for item in result.assignment_results) == p.assignments
    assert planning_service().validate_planning(planning(a), (), (), (), (availability(emp),)).is_valid() is True


def test_validate_planning_direct_affectations_invalides_sans_arret_au_premier_probleme():
    a = assignment(employee("Ada"))
    b = assignment(employee("Grace"))
    c = assignment(employee("Hedy"))
    p = planning(a, b, c)

    result = planning_service().validate_planning(p, (), (), (unavailability(a.employee),), (availability(b.employee),))

    assert result.valid is False
    assert [item.assignment for item in result.assignment_results] == [a, b, c]
    assert [item.is_valid() for item in result.assignment_results] == [False, True, False]
    assert result.invalid_assignment_count() == 2


def test_validate_planning_delegue_une_seule_fois_sans_preconsommer_les_generateurs():
    class SpyPlanningValidationService(PlanningValidationService):
        def __init__(self):
            super().__init__(assignment_service())
            self.calls = []

        def validate(self, assignments, qualification_requirements, employee_qualifications, unavailabilities, weekly_availabilities):
            self.calls.append((assignments, qualification_requirements, employee_qualifications, unavailabilities, weekly_availabilities))
            return super().validate(assignments, qualification_requirements, employee_qualifications, unavailabilities, weekly_availabilities)

    consumed = {"requirements": 0, "qualifications": 0, "unavailabilities": 0, "weekly": 0}
    emp = employee("Ada")
    req = requirement()
    a = assignment(emp, reqs=(req,))

    def requirements_gen():
        consumed["requirements"] += 1
        yield req

    def qualifications_gen():
        consumed["qualifications"] += 1
        yield EmployeeQualification(emp, req.qualification, QualificationStatus.VALID)

    def unavailabilities_gen():
        consumed["unavailabilities"] += 1
        if False:
            yield unavailability(emp)

    def weekly_gen():
        consumed["weekly"] += 1
        yield availability(emp)

    p = planning(a)
    service = SpyPlanningValidationService()
    result = service.validate_planning(p, requirements_gen(), qualifications_gen(), unavailabilities_gen(), weekly_gen())

    assert result.valid is True
    assert len(service.calls) == 1
    assert service.calls[0][0] is p.assignments
    assert consumed == {"requirements": 1, "qualifications": 1, "unavailabilities": 1, "weekly": 1}


@pytest.mark.parametrize("bad", [object(), None, "planning"])
def test_validate_planning_refuse_valeurs_non_planning(bad):
    with pytest.raises(ValueError, match="Le planning à valider doit être un Planning."):
        planning_service().validate_planning(bad, (), (), (), ())


def test_validate_planning_refuse_planning_vide_message_exact():
    with pytest.raises(ValueError, match="^Un planning sans affectation ne peut pas être validé\\.$"):
        planning_service().validate_planning(planning(), (), (), (), ())


@pytest.mark.parametrize("active", [True, False])
def test_validate_planning_accepte_planning_actif_et_inactif(active):
    emp = employee("Ada")
    assert planning_service().validate_planning(planning(assignment(emp), active=active), (), (), (), (availability(emp),)).is_valid()


@pytest.mark.parametrize("status", [PlanningStatus.DRAFT, PlanningStatus.VALIDATED, PlanningStatus.PUBLISHED, PlanningStatus.ARCHIVED])
def test_validate_planning_accepte_tous_les_statuts(status):
    emp = employee("Ada")
    assert planning_service().validate_planning(planning(assignment(emp), status=status), (), (), (), (availability(emp),)).is_valid()


def test_validate_planning_collections_annexes_listes_tuples_generateurs_refus_et_non_modification():
    emp = employee("Ada"); req = requirement(); a = assignment(emp, reqs=(req,))
    requirements = [req]
    employee_qualification = EmployeeQualification(emp, req.qualification, QualificationStatus.VALID)
    qualifications = (employee_qualification,)
    unavailabilities = []
    weekly_availability = availability(emp)
    weekly_items = [weekly_availability]

    result = planning_service().validate_planning(planning(a), requirements, qualifications, (item for item in unavailabilities), (item for item in weekly_items))

    assert result.valid is True
    assert requirements == [req]
    assert qualifications == (employee_qualification,)
    assert unavailabilities == []
    assert weekly_items == [weekly_availability]
    for bad in ("bad", b"bad"):
        with pytest.raises(ValueError):
            planning_service().validate_planning(planning(a), bad, (), (), ())
    with pytest.raises(ValueError, match="QualificationRequirement"):
        planning_service().validate_planning(planning(a), [object()], (), (), ())


def test_validate_planning_resultat_compatible_transition_draft_vers_validated():
    emp = employee("Ada")
    a = assignment(emp)
    p = planning(a, status=PlanningStatus.DRAFT)

    validation_result = planning_service().validate_planning(p, (), (), (), (availability(emp),))
    transition = PlanningStatusTransitionService().transition(p, PlanningStatus.VALIDATED, validation_result)

    assert validation_result.is_valid() is True
    assert transition.is_successful() is True
    assert p.status is PlanningStatus.DRAFT
    assert transition.updated_planning.status is PlanningStatus.VALIDATED
    assert transition.updated_planning.assignments == p.assignments


def test_validate_planning_resultat_invalide_refuse_transition_validation_failed():
    a = assignment(employee("Ada"))
    p = planning(a, status=PlanningStatus.DRAFT)

    validation_result = planning_service().validate_planning(p, (), (), (), ())
    transition = PlanningStatusTransitionService().transition(p, PlanningStatus.VALIDATED, validation_result)

    assert validation_result.is_valid() is False
    assert transition.failure.reason is PlanningStatusTransitionFailureReason.VALIDATION_FAILED
