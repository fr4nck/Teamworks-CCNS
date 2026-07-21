from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from uuid import UUID, uuid4

import pytest

from domain.missions import Mission, MissionOccurrence, MissionOccurrenceAssignment, MissionOccurrenceAssignmentStatus
from domain.people import Civility, Employee
from domain.planning import (
    AssignmentValidationIssue,
    AssignmentValidationIssueType,
    AssignmentValidationResult,
    Planning,
    PlanningStatus,
    PlanningStatusTransitionFailure,
    PlanningStatusTransitionFailureReason,
    PlanningStatusTransitionResult,
    PlanningStatusTransitionService,
    PlanningValidationResult,
)
from domain.qualifications import QualificationEligibilityResult


def employee(name="Ada"):
    return Employee(civility=Civility.MADAME, first_name=name, last_name="Lovelace")


def assignment(name="Ada", *, start=datetime(2026, 7, 20, 9), end=datetime(2026, 7, 20, 17), id=None):
    kwargs = {
        "employee": employee(name),
        "occurrence": MissionOccurrence(Mission(code=name, name="Animation"), starts_at=start, ends_at=end),
        "status": MissionOccurrenceAssignmentStatus.PLANNED,
    }
    if id is not None:
        kwargs["id"] = id
    return MissionOccurrenceAssignment(**kwargs)


def planning(*assignments, status=PlanningStatus.DRAFT, id=None):
    kwargs = {
        "code": "ETE-2026",
        "name": "Planning été",
        "starts_on": date(2026, 7, 1),
        "ends_on": date(2026, 7, 31),
        "assignments": assignments,
        "status": status,
    }
    if id is not None:
        kwargs["id"] = id
    return Planning(**kwargs)


def ok_validation(*assignments):
    return PlanningValidationResult(tuple(AssignmentValidationResult(a, True, ()) for a in assignments), True)


def ko_validation(assign):
    issue = AssignmentValidationIssue(
        AssignmentValidationIssueType.QUALIFICATION,
        QualificationEligibilityResult(assign.employee, assign.occurrence.mission, (), ()),
    )
    return PlanningValidationResult((AssignmentValidationResult(assign, False, (issue,)),), False)


def service():
    return PlanningStatusTransitionService()


@pytest.mark.parametrize(
    "current, requested",
    [
        (PlanningStatus.VALIDATED, PlanningStatus.DRAFT),
        (PlanningStatus.VALIDATED, PlanningStatus.PUBLISHED),
        (PlanningStatus.PUBLISHED, PlanningStatus.ARCHIVED),
        (PlanningStatus.ARCHIVED, PlanningStatus.DRAFT),
    ],
)
def test_transitions_autorisees_sans_validation(current, requested):
    p = planning(assignment(), status=current)
    result = service().transition(p, requested, validation_result=ok_validation(p.assignments[0]))
    assert result.is_successful() is True
    assert result.updated_planning is not p
    assert result.updated_planning.id == p.id
    assert result.updated_planning.status is requested
    assert p.status is current


def test_draft_vers_validated_exige_resultat_valide_correspondant_et_conserve_contenu():
    a = assignment("Ada"); b = assignment("Grace")
    p = planning(a, b)
    result = service().transition(p, PlanningStatus.VALIDATED, ok_validation(b, a))
    assert result.is_successful() is True
    assert result.has_updated_planning() is True
    assert result.has_failure() is False
    assert result.updated_planning.id == p.id
    assert result.updated_planning.assignments == (a, b)
    assert p.status is PlanningStatus.DRAFT


@pytest.mark.parametrize(
    "current, requested",
    [
        (PlanningStatus.DRAFT, PlanningStatus.DRAFT),
        (PlanningStatus.VALIDATED, PlanningStatus.VALIDATED),
        (PlanningStatus.PUBLISHED, PlanningStatus.PUBLISHED),
        (PlanningStatus.ARCHIVED, PlanningStatus.ARCHIVED),
    ],
)
def test_meme_statut_refuse(current, requested):
    result = service().transition(planning(assignment(), status=current), requested)
    assert result.successful is False
    assert result.failure.is_same_status() is True
    assert result.failure.message == "Le planning possède déjà le statut demandé."


@pytest.mark.parametrize(
    "current, requested",
    [
        (PlanningStatus.DRAFT, PlanningStatus.PUBLISHED),
        (PlanningStatus.DRAFT, PlanningStatus.ARCHIVED),
        (PlanningStatus.VALIDATED, PlanningStatus.ARCHIVED),
        (PlanningStatus.PUBLISHED, PlanningStatus.DRAFT),
        (PlanningStatus.PUBLISHED, PlanningStatus.VALIDATED),
        (PlanningStatus.ARCHIVED, PlanningStatus.VALIDATED),
        (PlanningStatus.ARCHIVED, PlanningStatus.PUBLISHED),
    ],
)
def test_transitions_non_autorisees_refusees(current, requested):
    result = service().transition(planning(assignment(), status=current), requested)
    assert result.successful is False
    assert result.failure.is_transition_not_allowed() is True
    assert result.failure.message == "La transition de statut demandée n’est pas autorisée."


def test_validation_requise_invalide_manquante_etrangere_et_plusieurs_affectations():
    a = assignment("Ada"); b = assignment("Grace"); foreign = assignment("Hedy")
    p = planning(a, b)
    assert service().transition(p, PlanningStatus.VALIDATED).failure.is_validation_required()
    assert service().transition(p, PlanningStatus.VALIDATED, ko_validation(a)).failure.is_validation_failed()
    assert service().transition(p, PlanningStatus.VALIDATED, ok_validation(a)).failure.is_validation_mismatch()
    assert service().transition(p, PlanningStatus.VALIDATED, ok_validation(a, b, foreign)).failure.is_validation_mismatch()
    assert service().transition(p, PlanningStatus.VALIDATED, ok_validation(a, foreign)).failure.is_validation_mismatch()


def test_comparaison_par_uuid_metier_et_planning_une_affectation():
    assignment_id = uuid4()
    original = assignment("Ada", id=assignment_id)
    equivalent = replace(original, employee=employee("Grace"))
    p = planning(original)
    result = service().transition(p, PlanningStatus.VALIDATED, ok_validation(equivalent))
    assert result.successful is True


def test_planning_vide_avec_resultat_incompatible_refuse():
    result = service().transition(planning(), PlanningStatus.VALIDATED, ok_validation(assignment()))
    assert result.failure.is_validation_mismatch() is True


def test_resultat_succes_et_echec_coherents_et_validations_strictes():
    p = planning(assignment())
    updated = p.with_status(PlanningStatus.VALIDATED)
    failure = PlanningStatusTransitionFailure(p, PlanningStatus.PUBLISHED, PlanningStatusTransitionFailureReason.TRANSITION_NOT_ALLOWED, "x")
    ok = PlanningStatusTransitionResult(p, PlanningStatus.VALIDATED, True, updated_planning=updated)
    assert ok.is_successful() and ok.has_updated_planning() and not ok.has_failure()
    ko = PlanningStatusTransitionResult(p, PlanningStatus.PUBLISHED, False, failure=failure)
    assert not ko.is_successful() and ko.has_failure() and not ko.has_updated_planning()
    with pytest.raises(ValueError, match="booléen"):
        PlanningStatusTransitionResult(p, PlanningStatus.VALIDATED, 1, updated_planning=updated)
    with pytest.raises(ValueError, match="ne doit pas contenir de planning"):
        PlanningStatusTransitionResult(p, PlanningStatus.PUBLISHED, False, updated_planning=updated, failure=failure)
    with pytest.raises(ValueError, match="ne doit pas contenir d'échec"):
        PlanningStatusTransitionResult(p, PlanningStatus.VALIDATED, True, updated_planning=updated, failure=failure)
    with pytest.raises(ValueError, match="UUID"):
        PlanningStatusTransitionResult(p, PlanningStatus.VALIDATED, True, updated_planning=planning(status=PlanningStatus.VALIDATED))
    with pytest.raises(ValueError, match="statut demandé"):
        PlanningStatusTransitionResult(p, PlanningStatus.PUBLISHED, True, updated_planning=updated)
    with pytest.raises(ValueError, match="planning d'origine"):
        PlanningStatusTransitionResult(planning(), PlanningStatus.PUBLISHED, False, failure=failure)
    with pytest.raises(ValueError, match="statut demandé"):
        PlanningStatusTransitionResult(p, PlanningStatus.ARCHIVED, False, failure=failure)


def test_objets_failure_uuid_message_immutabilite_et_methodes():
    p = planning()
    failure_id = uuid4()
    failure = PlanningStatusTransitionFailure(
        p, PlanningStatus.PUBLISHED, PlanningStatusTransitionFailureReason.VALIDATION_REQUIRED, "  message  ", id=failure_id
    )
    assert isinstance(PlanningStatusTransitionFailure(p, PlanningStatus.PUBLISHED, PlanningStatusTransitionFailureReason.SAME_STATUS, "x").id, UUID)
    assert failure.id == failure_id
    assert failure.message == "message" and failure.has_message() is True
    assert failure.is_validation_required() is True
    assert PlanningStatusTransitionFailure(p, PlanningStatus.PUBLISHED, PlanningStatusTransitionFailureReason.VALIDATION_FAILED, "x").is_validation_failed()
    assert PlanningStatusTransitionFailure(p, PlanningStatus.PUBLISHED, PlanningStatusTransitionFailureReason.VALIDATION_MISMATCH, "x").is_validation_mismatch()
    with pytest.raises(ValueError, match="UUID"):
        PlanningStatusTransitionFailure(p, PlanningStatus.PUBLISHED, PlanningStatusTransitionFailureReason.SAME_STATUS, "x", id="bad")
    with pytest.raises(ValueError, match="obligatoire"):
        PlanningStatusTransitionFailure(p, PlanningStatus.PUBLISHED, PlanningStatusTransitionFailureReason.SAME_STATUS, "  ")
    with pytest.raises(FrozenInstanceError):
        failure.message = "autre"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"planning": object(), "requested_status": PlanningStatus.DRAFT},
        {"planning": planning(), "requested_status": "draft"},
        {"planning": planning(), "requested_status": PlanningStatus.DRAFT, "reason": "same_status", "message": "x"},
    ],
)
def test_failure_refuse_types_invalides(kwargs):
    data = {"planning": planning(), "requested_status": PlanningStatus.DRAFT, "reason": PlanningStatusTransitionFailureReason.SAME_STATUS, "message": "x"}
    data.update(kwargs)
    with pytest.raises(ValueError):
        PlanningStatusTransitionFailure(**data)


def test_service_valide_strictement_les_entrees_et_ignore_validation_inutile():
    p = planning(assignment(), status=PlanningStatus.VALIDATED)
    validation = ok_validation(p.assignments[0])
    assert service().transition(p, PlanningStatus.PUBLISHED, validation).successful is True
    with pytest.raises(ValueError, match="Planning"):
        service().transition(object(), PlanningStatus.DRAFT)
    with pytest.raises(ValueError, match="PlanningStatus"):
        service().transition(p, "draft")
    with pytest.raises(ValueError, match="PlanningValidationResult"):
        service().transition(p, PlanningStatus.DRAFT, object())
