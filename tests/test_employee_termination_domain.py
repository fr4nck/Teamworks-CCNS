from datetime import date, datetime, timezone

import pytest

from domain.employment.termination import (
    CheckState,
    ContractTermination,
    HrInputChecks,
    NoticeStatus,
    TerminationDomainError,
    TerminationReason,
    TerminationWorkflowStatus,
)


def dt(day: int) -> datetime:
    return datetime(2026, 10, day, 9, 0, tzinfo=timezone.utc)


def ready_termination(**overrides):
    values = dict(
        contract_id="contract-1",
        effective_end_date=date(2026, 10, 31),
        known_at=dt(1),
        last_worked_date=date(2026, 10, 31),
        created_by="director-1",
        created_at=dt(2),
        termination_reason=TerminationReason.END_OF_FIXED_TERM,
        notice_status=NoticeStatus.NONE,
        hr_checks=HrInputChecks(
            hours=CheckState.NONE,
            absences=CheckState.NONE,
            leave=CheckState.PROVIDED,
            variable_pay=CheckState.NONE,
            exceptional_items=CheckState.NONE,
        ),
    )
    values.update(overrides)
    return ContractTermination(**values)


def assert_error(code, callable_):
    with pytest.raises(TerminationDomainError) as exc:
        callable_()
    assert exc.value.code == code


def test_contract_id_is_required():
    assert_error("CONTRACT_ID_REQUIRED", lambda: ready_termination(contract_id=" "))


def test_last_worked_date_cannot_be_after_effective_end():
    assert_error(
        "LAST_WORKED_AFTER_END",
        lambda: ready_termination(last_worked_date=date(2026, 11, 1)),
    )


def test_end_cannot_precede_contract_start_when_checked():
    termination = ready_termination()
    assert_error(
        "END_BEFORE_CONTRACT_START",
        lambda: termination.validate_against_contract_start(date(2026, 11, 1)),
    )


def test_known_at_cannot_be_after_recording():
    assert_error("KNOWN_AFTER_RECORDED", lambda: ready_termination(known_at=dt(3), created_at=dt(2)))


def test_late_discovery_and_late_recording_are_derived_independently():
    termination = ready_termination(
        effective_end_date=date(2026, 10, 10),
        last_worked_date=date(2026, 10, 10),
        known_at=dt(14),
        created_at=dt(15),
    )
    assert termination.late_discovery is True
    assert termination.late_recording is True


def test_unknown_none_and_provided_are_distinct():
    assert len({CheckState.UNKNOWN, CheckState.NONE, CheckState.PROVIDED}) == 3


def test_unknown_reason_blocks_ready():
    termination = ready_termination(termination_reason=TerminationReason.UNKNOWN)
    assert "TERMINATION_REASON_UNKNOWN" in termination.readiness_errors()
    assert_error(
        "TERMINATION_REASON_UNKNOWN",
        lambda: termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI),
    )


def test_unknown_notice_blocks_ready():
    termination = ready_termination(notice_status=NoticeStatus.UNKNOWN)
    assert "NOTICE_STATUS_UNKNOWN" in termination.readiness_errors()


def test_provided_notice_requires_both_dates():
    assert_error(
        "NOTICE_DATES_REQUIRED",
        lambda: ready_termination(notice_status=NoticeStatus.PROVIDED, notice_start=date(2026, 10, 1)),
    )


def test_provided_notice_dates_must_be_ordered():
    assert_error(
        "NOTICE_DATES_INVALID",
        lambda: ready_termination(
            notice_status=NoticeStatus.PROVIDED,
            notice_start=date(2026, 10, 20),
            notice_end=date(2026, 10, 10),
        ),
    )


def test_none_notice_rejects_dates():
    assert_error(
        "NOTICE_NONE_WITH_DATES",
        lambda: ready_termination(notice_status=NoticeStatus.NONE, notice_start=date(2026, 10, 1)),
    )


@pytest.mark.parametrize("field", ["hours", "absences", "leave", "variable_pay", "exceptional_items"])
def test_each_unknown_hr_check_blocks_ready(field):
    checks = {name: CheckState.NONE for name in ("hours", "absences", "leave", "variable_pay", "exceptional_items")}
    checks[field] = CheckState.UNKNOWN
    termination = ready_termination(hr_checks=HrInputChecks(**checks))
    assert f"HR_CHECK_{field.upper()}_UNKNOWN" in termination.readiness_errors()
    assert termination.can_be_ready_for_impact_emploi() is False


def test_none_and_provided_hr_checks_are_both_ready_values():
    termination = ready_termination()
    assert termination.can_be_ready_for_impact_emploi() is True
    termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    assert termination.workflow_status is TerminationWorkflowStatus.PRET_IMPACT_EMPLOI


def test_workflow_rejects_skipping_steps():
    termination = ready_termination()
    assert_error(
        "INVALID_WORKFLOW_TRANSITION",
        lambda: termination.transition_to(TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI),
    )


def test_transmitted_data_cannot_be_silently_modified():
    termination = ready_termination()
    termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    termination.transition_to(TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI)
    assert_error(
        "CORRECTION_REQUIRED",
        lambda: termination.update_transmittable(effective_end_date=date(2026, 10, 30)),
    )


def test_closure_requires_explicit_external_checklist_and_is_not_automatic():
    termination = ready_termination()
    for target in (
        TerminationWorkflowStatus.PRET_IMPACT_EMPLOI,
        TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI,
        TerminationWorkflowStatus.EN_ATTENTE_RESULTATS,
        TerminationWorkflowStatus.RESULTATS_RECUS,
        TerminationWorkflowStatus.DOCUMENTS_REMIS,
    ):
        termination.transition_to(target)
    assert_error(
        "CLOSURE_CHECKLIST_INCOMPLETE",
        lambda: termination.transition_to(TerminationWorkflowStatus.CLOTURE),
    )
    termination.transition_to(TerminationWorkflowStatus.CLOTURE, external_checklist_complete=True)
    assert termination.workflow_status is TerminationWorkflowStatus.CLOTURE
    assert_error("TERMINATION_CLOSED", lambda: termination.update_transmittable(comments="late edit"))


def test_version_increments_on_successful_mutation_for_future_optimistic_locking():
    termination = ready_termination()
    assert termination.version == 0
    termination.update_transmittable(comments="checked")
    assert termination.version == 1
    termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    assert termination.version == 2


def test_failed_mutation_restores_previous_values():
    termination = ready_termination()
    previous_end = termination.effective_end_date
    assert_error(
        "LAST_WORKED_AFTER_END",
        lambda: termination.update_transmittable(effective_end_date=date(2026, 10, 1)),
    )
    assert termination.effective_end_date == previous_end
