from datetime import date, datetime, timezone

import pytest

from application.services.hr_connections import HrCaseWorkflowService
from domain.hr_connections import (
    HrCase,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrEventKind,
    HrEventTargetKind,
)


class FakeWorkflowRepository:
    def __init__(self, case=None):
        self.case = case
        self.persist_calls = []

    def get_case(self, *, structure_ref, case_id):
        if self.case is None or self.case.case_id != case_id:
            return None
        return self.case

    def persist_case_transition(
        self,
        *,
        structure_ref,
        expected_status,
        case,
        event,
    ):
        self.persist_calls.append(
            (structure_ref, expected_status, case, event)
        )
        self.case = case
        return case


def _case(status=HrCaseStatus.TODO):
    return HrCase(
        case_id="case-1",
        case_type=HrCaseType.create(code="dpae", label="DPAE"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code="urssaf",
        opened_on=date(2026, 9, 1),
        due_on=date(2026, 9, 3),
        status=status,
    )


def _service(repository):
    return HrCaseWorkflowService(
        repository=repository,
        now_provider=lambda: datetime(2026, 9, 1, 20, 0, tzinfo=timezone.utc),
        event_id_factory=lambda: "evt-transition-1",
    )


def test_available_transitions_come_from_domain_state_machine():
    service = _service(FakeWorkflowRepository(_case()))

    options = service.available_transitions(
        structure_ref="structure-a",
        case_id="case-1",
    )

    assert options.case.status is HrCaseStatus.TODO
    assert options.allowed_statuses == (
        HrCaseStatus.PREPARED,
        HrCaseStatus.CANCELLED,
    )


def test_transition_persists_case_and_append_only_event_as_one_port_call():
    repository = FakeWorkflowRepository(_case())
    service = _service(repository)

    result = service.transition(
        structure_ref="structure-a",
        case_id="case-1",
        status=HrCaseStatus.PREPARED,
        actor_ref=" user-7 ",
        source=" teamworks-ui ",
        comment="Dossier prêt",
    )

    assert result.case.status is HrCaseStatus.PREPARED
    assert result.case.comment == "Dossier prêt"
    assert result.event.event_id == "evt-transition-1"
    assert result.event.kind is HrEventKind.CASE_STATUS_CHANGED
    assert result.event.target_kind is HrEventTargetKind.CASE
    assert result.event.target_ref == "case-1"
    assert result.event.actor_ref == "user-7"
    assert result.event.source == "teamworks-ui"
    assert [(field.key, field.value) for field in result.event.fields] == [
        ("from_status", "todo"),
        ("to_status", "prepared"),
    ]

    assert len(repository.persist_calls) == 1
    structure_ref, expected_status, persisted_case, event = repository.persist_calls[0]
    assert structure_ref == "structure-a"
    assert expected_status is HrCaseStatus.TODO
    assert persisted_case is result.case
    assert event is result.event


def test_illegal_transition_is_rejected_before_persistence():
    repository = FakeWorkflowRepository(_case())
    service = _service(repository)

    with pytest.raises(ValueError):
        service.transition(
            structure_ref="structure-a",
            case_id="case-1",
            status=HrCaseStatus.ACCEPTED,
        )

    assert repository.persist_calls == []


def test_missing_case_is_explicit():
    service = _service(FakeWorkflowRepository())

    with pytest.raises(LookupError):
        service.available_transitions(
            structure_ref="structure-a",
            case_id="missing",
        )


def test_transition_requires_timezone_aware_clock():
    repository = FakeWorkflowRepository(_case())
    service = HrCaseWorkflowService(
        repository=repository,
        now_provider=lambda: datetime(2026, 9, 1, 20, 0),
        event_id_factory=lambda: "evt-transition-1",
    )

    with pytest.raises(ValueError):
        service.transition(
            structure_ref="structure-a",
            case_id="case-1",
            status=HrCaseStatus.PREPARED,
        )

    assert repository.persist_calls == []


def test_transition_requires_non_empty_event_identifier_and_source():
    repository = FakeWorkflowRepository(_case())
    service = HrCaseWorkflowService(
        repository=repository,
        now_provider=lambda: datetime(2026, 9, 1, 20, 0, tzinfo=timezone.utc),
        event_id_factory=lambda: "   ",
    )

    with pytest.raises(ValueError):
        service.transition(
            structure_ref="structure-a",
            case_id="case-1",
            status=HrCaseStatus.PREPARED,
        )

    with pytest.raises(ValueError):
        _service(repository).transition(
            structure_ref="structure-a",
            case_id="case-1",
            status=HrCaseStatus.PREPARED,
            source="   ",
        )
