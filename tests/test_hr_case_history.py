from datetime import datetime, timezone

import pytest

from application.services.hr_connections import HrCaseHistoryService
from domain.hr_connections import (
    HrAuditEvent,
    HrAuditField,
    HrEventKind,
    HrEventTargetKind,
)


class FakeRepository:
    def __init__(self, events=()):
        self.events = tuple(events)
        self.calls = []

    def list_events(self, *, structure_ref, target_kind=None, target_ref=None):
        self.calls.append((structure_ref, target_kind, target_ref))
        return tuple(
            event
            for event in self.events
            if (target_kind is None or event.target_kind is target_kind)
            and (target_ref is None or event.target_ref == target_ref)
        )


def _event(event_id, minute, kind=HrEventKind.CASE_STATUS_CHANGED, target_ref="case-1"):
    return HrAuditEvent.create(
        event_id=event_id,
        kind=kind,
        target_kind=HrEventTargetKind.CASE,
        target_ref=target_ref,
        occurred_at=datetime(2026, 9, 1, 20, minute, tzinfo=timezone.utc),
        actor_ref="user-1",
        source="teamworks-ui",
        fields=(
            HrAuditField.create(key="from_status", value="todo"),
            HrAuditField.create(key="to_status", value="prepared"),
        ),
    )


def test_history_filters_case_events_and_sorts_newest_first():
    repository = FakeRepository(
        (
            _event("evt-1", 1),
            _event("evt-other", 3, target_ref="case-2"),
            _event("evt-2", 2, kind=HrEventKind.RETURN_IMPORTED),
        )
    )
    service = HrCaseHistoryService(repository=repository)

    history = service.build(structure_ref="structure-a", case_id="case-1")

    assert repository.calls == [
        ("structure-a", HrEventTargetKind.CASE, "case-1")
    ]
    assert [row.event_id for row in history.rows] == ["evt-2", "evt-1"]
    assert history.total_count == 2
    assert history.status_change_count == 1
    assert history.latest_at == history.rows[0].occurred_at
    assert history.rows[1].fields[0].key == "from_status"


def test_empty_history_is_explicit():
    history = HrCaseHistoryService(repository=FakeRepository()).build(
        structure_ref="structure-a",
        case_id="case-1",
    )

    assert history.is_empty
    assert history.total_count == 0
    assert history.latest_at is None


def test_history_rejects_invalid_repository_payload():
    class InvalidRepository:
        def list_events(self, **kwargs):
            return (object(),)

    service = HrCaseHistoryService(repository=InvalidRepository())

    with pytest.raises(TypeError):
        service.build(structure_ref="structure-a", case_id="case-1")


def test_history_rejects_foreign_event_even_if_repository_ignores_filter():
    class LeakyRepository:
        def list_events(self, **kwargs):
            return (_event("evt-other", 1, target_ref="case-2"),)

    service = HrCaseHistoryService(repository=LeakyRepository())

    with pytest.raises(ValueError):
        service.build(structure_ref="structure-a", case_id="case-1")


@pytest.mark.parametrize("structure_ref, case_id", [("", "case-1"), ("structure-a", "")])
def test_history_requires_structure_and_case_identifiers(structure_ref, case_id):
    service = HrCaseHistoryService(repository=FakeRepository())

    with pytest.raises(ValueError):
        service.build(structure_ref=structure_ref, case_id=case_id)
