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


def transmit(termination):
    from tests.termination_transmission_support import transmit_in_memory
    return transmit_in_memory(termination)


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
    transmit(termination)
    assert termination.workflow_status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI
    assert_error(
        "CORRECTION_REQUIRED",
        lambda: termination.update_transmittable(effective_end_date=date(2026, 10, 30)),
    )


def test_closure_requires_explicit_external_checklist_and_is_not_automatic():
    termination = ready_termination()
    transmit(termination)
    for target in (
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


def test_domain_mutations_do_not_advance_persisted_version():
    # La version est la révision persistée attendue par l'optimistic locking :
    # seul le repository la fait avancer (+1 par sauvegarde), jamais le domaine,
    # sinon une seule mutation donnerait N -> N+1 (domaine) -> N+2 (SQL).
    termination = ready_termination()
    assert termination.version == 0
    before = termination.updated_at
    termination.update_transmittable(comments="checked")
    termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    assert termination.version == 0
    assert termination.updated_at >= before


def test_textual_states_read_back_from_storage_are_coerced_and_still_block():
    termination = ready_termination(
        termination_reason="UNKNOWN",
        notice_status="NONE",
        workflow_status="A_PREPARER",
        hr_checks=HrInputChecks(
            hours="UNKNOWN", absences="NONE", leave="PROVIDED",
            variable_pay="NONE", exceptional_items="NONE",
        ),
    )
    assert termination.termination_reason is TerminationReason.UNKNOWN
    assert termination.hr_checks.hours is CheckState.UNKNOWN
    assert termination.workflow_status is TerminationWorkflowStatus.A_PREPARER
    assert termination.readiness_errors() == (
        "TERMINATION_REASON_UNKNOWN",
        "HR_CHECK_HOURS_UNKNOWN",
    )


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"notice_status": "PEUT-ETRE"}, "INVALID_NOTICE_STATUS"),
        ({"termination_reason": "ABANDON"}, "INVALID_TERMINATION_REASON"),
        ({"workflow_status": "ARCHIVE"}, "INVALID_WORKFLOW_STATUS"),
    ],
)
def test_invalid_textual_states_are_rejected(overrides, code):
    assert_error(code, lambda: ready_termination(**overrides))


def test_invalid_hr_check_state_is_rejected():
    assert_error("INVALID_HR_CHECK_STATE", lambda: HrInputChecks(hours="MAYBE"))


def test_ready_termination_cannot_silently_become_unknown_again():
    termination = ready_termination()
    termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    previous_checks = termination.hr_checks
    assert_error(
        "HR_CHECK_HOURS_UNKNOWN",
        lambda: termination.update_transmittable(hr_checks=HrInputChecks()),
    )
    assert_error(
        "TERMINATION_REASON_UNKNOWN",
        lambda: termination.update_transmittable(termination_reason=TerminationReason.UNKNOWN),
    )
    assert termination.hr_checks == previous_checks
    assert termination.termination_reason is TerminationReason.END_OF_FIXED_TERM
    assert termination.workflow_status is TerminationWorkflowStatus.PRET_IMPACT_EMPLOI


def test_naive_timestamps_are_rejected_with_domain_error():
    assert_error(
        "TIMESTAMP_TIMEZONE_REQUIRED",
        lambda: ready_termination(known_at=datetime(2026, 10, 1, 9, 0)),
    )


def test_invalid_update_type_is_a_domain_error_and_restores_state():
    termination = ready_termination()
    assert_error(
        "EFFECTIVE_END_DATE_REQUIRED",
        lambda: termination.update_transmittable(effective_end_date="2026-10-30"),
    )
    assert termination.effective_end_date == date(2026, 10, 31)


def test_failed_mutation_restores_previous_values():
    termination = ready_termination()
    previous_end = termination.effective_end_date
    assert_error(
        "LAST_WORKED_AFTER_END",
        lambda: termination.update_transmittable(effective_end_date=date(2026, 10, 1)),
    )
    assert termination.effective_end_date == previous_end
