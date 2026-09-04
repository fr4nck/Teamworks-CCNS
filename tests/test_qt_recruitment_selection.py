from __future__ import annotations

import sys
from pathlib import Path

import pytest


QT_THEME_DIR = Path(__file__).resolve().parents[1] / "poc" / "qt-theme"
if str(QT_THEME_DIR) not in sys.path:
    sys.path.insert(0, str(QT_THEME_DIR))

from recruitment_selection import (  # noqa: E402
    ActionTarget,
    ApplicationSelection,
    CandidateSubject,
    IntegrityWarning,
    InterviewSelection,
    JobOfferRelation,
    JobOfferSubject,
    PersonSubject,
    RecruitmentMode,
    RecruitmentUiState,
    RowKind,
    SelectionError,
    SpontaneousApplication,
    application_matches_subject,
    interview_matches_subject,
    resolve_application_selection,
    resolve_candidate_selection,
    resolve_interview_selection,
    resolve_job_selection,
)


def _exists(*ids: int):
    known = set(ids)
    return lambda value: value in known


@pytest.mark.parametrize("bad_id", [None, 0, -1, True, False, "42", 42.0])
def test_candidate_requires_a_real_positive_integer_identifier(bad_id):
    result = resolve_candidate_selection(bad_id)

    assert result.ok is False
    assert result.selection is None
    assert result.error in {SelectionError.MISSING_ROW_ID, SelectionError.INVALID_ROW_ID}


def test_candidate_not_found_never_builds_a_summary_subject():
    result = resolve_candidate_selection(42, candidate_exists=_exists())

    assert result.error == SelectionError.CANDIDATE_NOT_FOUND
    assert result.selection is None


@pytest.mark.parametrize("person_id", [None, 0])
def test_application_without_person_uses_candidate_subject(person_id):
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=person_id,
        job_id=0,
        candidate_exists=_exists(27),
    )

    assert result.ok
    assert result.selection.subject == CandidateSubject(27)
    assert isinstance(result.selection.job_relation, SpontaneousApplication)


def test_application_with_person_uses_person_subject_even_when_candidate_is_present():
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=83,
        job_id=12,
        candidate_exists=_exists(27),
        person_exists=_exists(83),
        job_exists=_exists(12),
    )

    assert result.ok
    assert result.selection.subject == PersonSubject(83)
    assert result.selection.candidate_id == 27
    assert isinstance(result.selection.job_relation, JobOfferRelation)
    assert result.selection.job_relation.job_id == 12


def test_broken_person_reference_never_falls_back_to_valid_candidate():
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=83,
        job_id=0,
        candidate_exists=_exists(27),
        person_exists=_exists(),
    )

    assert result.ok is False
    assert result.error == SelectionError.PERSON_NOT_FOUND
    assert result.selection is None


def test_valid_person_can_be_displayed_while_broken_candidate_reference_is_reported():
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=83,
        job_id=0,
        candidate_exists=_exists(),
        person_exists=_exists(83),
    )

    assert result.ok
    assert result.selection.subject == PersonSubject(83)
    assert result.warnings == (IntegrityWarning.CANDIDATE_REFERENCE_BROKEN,)


@pytest.mark.parametrize("candidate_id, person_id", [(None, None), (0, 0)])
def test_application_without_any_identity_reference_is_rejected(candidate_id, person_id):
    result = resolve_application_selection(
        154,
        candidate_id=candidate_id,
        person_id=person_id,
        job_id=0,
    )

    assert result.error == SelectionError.NO_IDENTITY_REFERENCE
    assert result.selection is None


@pytest.mark.parametrize(
    "candidate_id, person_id",
    [
        (27.0, 0),
        ("27", 0),
        (True, 0),
        (27, 83.0),
        (27, "83"),
        (27, True),
        (-27, 0),
        (27, -83),
    ],
)
def test_application_rejects_invalid_identity_reference_types(candidate_id, person_id):
    result = resolve_application_selection(
        154,
        candidate_id=candidate_id,
        person_id=person_id,
        job_id=0,
    )

    assert result.error == SelectionError.INVALID_REFERENCE_ID
    assert result.selection is None


@pytest.mark.parametrize("zero_like", [0.0, False])
def test_application_does_not_silently_coerce_non_integer_zero_identity_reference(zero_like):
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=zero_like,
        job_id=0,
    )

    assert result.error == SelectionError.INVALID_REFERENCE_ID
    assert result.selection is None


def test_zero_job_id_is_valid_only_as_spontaneous_application_relation():
    application = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=0,
        job_id=0,
        candidate_exists=_exists(27),
    )
    job = resolve_job_selection(0)

    assert application.ok
    assert isinstance(application.selection.job_relation, SpontaneousApplication)
    assert job.ok is False
    assert job.error == SelectionError.INVALID_ROW_ID


def test_missing_job_reference_does_not_replace_a_valid_identity():
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=83,
        job_id=12,
        candidate_exists=_exists(27),
        person_exists=_exists(83),
        job_exists=_exists(),
    )

    assert result.ok
    assert result.selection.subject == PersonSubject(83)
    assert IntegrityWarning.JOB_REFERENCE_BROKEN in result.warnings


@pytest.mark.parametrize("bad_job_id", [None, -1, True, False, "12", 12.0])
def test_application_rejects_invalid_job_reference_values(bad_job_id):
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=0,
        job_id=bad_job_id,
    )

    assert result.error == SelectionError.INVALID_REFERENCE_ID
    assert result.selection is None


def test_interview_with_person_uses_person_without_falling_back_to_candidate():
    result = resolve_interview_selection(
        77,
        candidate_id=27,
        person_id=83,
        candidate_exists=_exists(27),
        person_exists=_exists(83),
    )

    assert result.ok
    assert result.selection.subject == PersonSubject(83)


def test_broken_interview_person_reference_never_falls_back_to_candidate():
    result = resolve_interview_selection(
        77,
        candidate_id=27,
        person_id=83,
        candidate_exists=_exists(27),
        person_exists=_exists(),
    )

    assert result.error == SelectionError.PERSON_NOT_FOUND
    assert result.selection is None


def test_candidate_summary_rejects_application_that_has_become_a_person():
    result = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=83,
        job_id=0,
    )
    selection = result.selection

    assert isinstance(selection, ApplicationSelection)
    assert application_matches_subject(selection, CandidateSubject(27)) is False
    assert application_matches_subject(selection, PersonSubject(83)) is True


def test_person_summary_rejects_application_for_another_person():
    result = resolve_application_selection(
        155,
        candidate_id=27,
        person_id=84,
        job_id=0,
    )

    assert application_matches_subject(result.selection, PersonSubject(83)) is False


def test_job_summary_only_accepts_applications_linked_to_that_job():
    linked = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=0,
        job_id=12,
    ).selection
    other_job = resolve_application_selection(
        155,
        candidate_id=27,
        person_id=0,
        job_id=14,
    ).selection
    spontaneous = resolve_application_selection(
        156,
        candidate_id=27,
        person_id=0,
        job_id=0,
    ).selection

    assert application_matches_subject(linked, JobOfferSubject(12)) is True
    assert application_matches_subject(other_job, JobOfferSubject(12)) is False
    assert application_matches_subject(spontaneous, JobOfferSubject(12)) is False


def test_person_summary_rejects_interview_for_another_person():
    result = resolve_interview_selection(
        77,
        candidate_id=27,
        person_id=84,
    )

    assert isinstance(result.selection, InterviewSelection)
    assert interview_matches_subject(result.selection, PersonSubject(83)) is False


def test_candidate_summary_rejects_interview_for_another_candidate():
    result = resolve_interview_selection(
        77,
        candidate_id=28,
        person_id=0,
    )

    assert interview_matches_subject(result.selection, CandidateSubject(27)) is False


def test_application_action_target_is_application_not_summary_person():
    state = RecruitmentUiState(RecruitmentMode.APPLICATIONS)
    selection = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=83,
        job_id=0,
    ).selection

    state.set_selection(selection)

    assert state.selection.subject == PersonSubject(83)
    assert state.action_target() == ActionTarget(RowKind.APPLICATION, 154)


def test_interview_action_target_is_interview_not_summary_candidate():
    state = RecruitmentUiState(RecruitmentMode.INTERVIEWS)
    selection = resolve_interview_selection(
        77,
        candidate_id=27,
        person_id=0,
    ).selection

    state.set_selection(selection)

    assert state.selection.subject == CandidateSubject(27)
    assert state.action_target() == ActionTarget(RowKind.INTERVIEW, 77)


def test_two_applications_for_same_person_keep_distinct_action_targets():
    state = RecruitmentUiState(RecruitmentMode.APPLICATIONS)
    first = resolve_application_selection(
        155,
        candidate_id=27,
        person_id=83,
        job_id=0,
    ).selection
    second = resolve_application_selection(
        156,
        candidate_id=27,
        person_id=83,
        job_id=0,
    ).selection

    state.set_selection(first)
    assert state.action_target() == ActionTarget(RowKind.APPLICATION, 155)

    state.set_selection(second)
    assert state.selection.subject == PersonSubject(83)
    assert state.action_target() == ActionTarget(RowKind.APPLICATION, 156)


def test_changing_mode_clears_selection_and_action_target():
    state = RecruitmentUiState(RecruitmentMode.APPLICATIONS)
    selection = resolve_application_selection(
        154,
        candidate_id=27,
        person_id=83,
        job_id=0,
    ).selection
    state.set_selection(selection)

    state.change_mode(RecruitmentMode.JOBS)

    assert state.selection is None
    assert state.action_target() is None


def test_selection_from_wrong_mode_is_rejected():
    state = RecruitmentUiState(RecruitmentMode.CANDIDATES)
    selection = resolve_job_selection(12).selection

    with pytest.raises(ValueError, match=SelectionError.MODE_MISMATCH.value):
        state.set_selection(selection)

    assert state.selection is None


def test_late_summary_response_cannot_restore_old_action_target():
    state = RecruitmentUiState(RecruitmentMode.APPLICATIONS)
    first = resolve_application_selection(
        155,
        candidate_id=27,
        person_id=83,
        job_id=0,
    ).selection
    second = resolve_application_selection(
        156,
        candidate_id=27,
        person_id=83,
        job_id=0,
    ).selection

    first_revision = state.set_selection(first)
    second_revision = state.set_selection(second)

    assert state.accepts_response(first_revision, PersonSubject(83)) is False
    assert state.accepts_response(second_revision, PersonSubject(83)) is True
    assert state.action_target() == ActionTarget(RowKind.APPLICATION, 156)


def test_response_for_previous_subject_is_rejected_even_with_current_revision():
    state = RecruitmentUiState(RecruitmentMode.CANDIDATES)
    candidate = resolve_candidate_selection(42).selection
    revision = state.set_selection(candidate)

    assert state.accepts_response(revision, CandidateSubject(43)) is False
    assert state.accepts_response(revision, CandidateSubject(42)) is True
