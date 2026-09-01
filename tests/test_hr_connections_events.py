from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from domain.hr_connections import (
    HrAuditEvent,
    HrAuditField,
    HrEventJournal,
    HrEventKind,
    HrEventTargetKind,
)


def _event(
    *,
    event_id: str = "EVT-001",
    kind: HrEventKind = HrEventKind.CASE_CREATED,
    target_kind: HrEventTargetKind = HrEventTargetKind.CASE,
    target_ref: str = "CASE-001",
) -> HrAuditEvent:
    return HrAuditEvent.create(
        event_id=event_id,
        kind=kind,
        target_kind=target_kind,
        target_ref=target_ref,
        occurred_at=datetime(2026, 9, 1, 8, 30, tzinfo=timezone.utc),
        actor_ref=" direction ",
        source=" teamworks ",
        fields=[HrAuditField.create(key=" statut ", value=" todo ")],
    )


def test_audit_field_normalizes_key_and_value():
    field = HrAuditField.create(key=" Reference Externe ", value=" ABC-123 ")

    assert field.key == "reference_externe"
    assert field.value == "ABC-123"


def test_audit_field_rejects_empty_and_obviously_sensitive_keys():
    with pytest.raises(ValueError):
        HrAuditField.create(key=" ", value="value")
    with pytest.raises(ValueError):
        HrAuditField.create(key="reference", value=" ")

    for key in (
        "password",
        "mot de passe",
        "access-token",
        "refresh_token",
        "api key",
        "private-key",
        "medical data",
        "diagnosis",
    ):
        with pytest.raises(ValueError):
            HrAuditField.create(key=key, value="ne-doit-pas-etre-journalise")


def test_audit_event_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError):
        HrAuditEvent.create(
            event_id="EVT",
            kind=HrEventKind.CASE_CREATED,
            target_kind=HrEventTargetKind.CASE,
            target_ref="CASE-001",
            occurred_at=datetime(2026, 9, 1, 8, 30),
        )


def test_audit_event_requires_stable_identity_and_typed_target():
    timestamp = datetime(2026, 9, 1, 8, 30, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        HrAuditEvent.create(
            event_id=" ",
            kind=HrEventKind.CASE_CREATED,
            target_kind=HrEventTargetKind.CASE,
            target_ref="CASE-001",
            occurred_at=timestamp,
        )
    with pytest.raises(ValueError):
        HrAuditEvent.create(
            event_id="EVT",
            kind=HrEventKind.CASE_CREATED,
            target_kind=HrEventTargetKind.CASE,
            target_ref=" ",
            occurred_at=timestamp,
        )
    with pytest.raises(TypeError):
        HrAuditEvent(
            event_id="EVT",
            kind="case_created",  # type: ignore[arg-type]
            target_kind=HrEventTargetKind.CASE,
            target_ref="CASE-001",
            occurred_at=timestamp,
        )
    with pytest.raises(TypeError):
        HrAuditEvent(
            event_id="EVT",
            kind=HrEventKind.CASE_CREATED,
            target_kind="case",  # type: ignore[arg-type]
            target_ref="CASE-001",
            occurred_at=timestamp,
        )


def test_audit_event_rejects_duplicate_field_keys():
    with pytest.raises(ValueError):
        HrAuditEvent.create(
            event_id="EVT",
            kind=HrEventKind.CASE_STATUS_CHANGED,
            target_kind=HrEventTargetKind.CASE,
            target_ref="CASE-001",
            occurred_at=datetime(2026, 9, 1, 8, 30, tzinfo=timezone.utc),
            fields=[
                HrAuditField.create(key="status", value="todo"),
                HrAuditField.create(key="status", value="prepared"),
            ],
        )


def test_audit_event_is_immutable_and_normalizes_non_sensitive_refs():
    event = _event()

    assert event.event_id == "EVT-001"
    assert event.actor_ref == "direction"
    assert event.source == "teamworks"
    assert event.fields[0].key == "statut"

    with pytest.raises(FrozenInstanceError):
        event.event_id = "OTHER"  # type: ignore[misc]


def test_journal_is_append_only_and_preserves_insertion_order():
    first = _event(event_id="EVT-001")
    second = _event(
        event_id="EVT-002",
        kind=HrEventKind.CASE_STATUS_CHANGED,
    )
    journal = HrEventJournal()

    journal.append(first)
    journal.append(second)

    assert len(journal) == 2
    assert journal.all() == (first, second)
    assert isinstance(journal.all(), tuple)
    assert not hasattr(journal, "update")
    assert not hasattr(journal, "delete")
    assert not hasattr(journal, "remove")


def test_journal_rejects_duplicate_event_ids_and_invalid_objects():
    journal = HrEventJournal([_event(event_id="EVT-001")])

    with pytest.raises(ValueError):
        journal.append(_event(event_id="EVT-001", kind=HrEventKind.SYNC_STARTED))
    with pytest.raises(TypeError):
        journal.append("event")  # type: ignore[arg-type]


def test_journal_filters_by_target_without_exposing_internal_list():
    case_one = _event(event_id="EVT-001", target_ref="CASE-001")
    case_two = _event(event_id="EVT-002", target_ref="CASE-002")
    connector = _event(
        event_id="EVT-003",
        kind=HrEventKind.CONNECTOR_CONFIGURATION_CHANGED,
        target_kind=HrEventTargetKind.CONNECTOR,
        target_ref="urssaf-manual",
    )
    journal = HrEventJournal([case_one, case_two, connector])

    assert journal.for_target(
        target_kind=HrEventTargetKind.CASE,
        target_ref=" CASE-001 ",
    ) == (case_one,)
    assert journal.for_target(
        target_kind=HrEventTargetKind.CONNECTOR,
        target_ref="urssaf-manual",
    ) == (connector,)


def test_journal_filters_by_event_kind():
    created = _event(event_id="EVT-001")
    changed = _event(event_id="EVT-002", kind=HrEventKind.CASE_STATUS_CHANGED)
    journal = HrEventJournal([created, changed])

    assert journal.for_kind(HrEventKind.CASE_CREATED) == (created,)
    assert journal.for_kind(HrEventKind.CASE_STATUS_CHANGED) == (changed,)
    with pytest.raises(TypeError):
        journal.for_kind("case_created")  # type: ignore[arg-type]


def test_journal_validates_target_filters():
    journal = HrEventJournal()

    with pytest.raises(TypeError):
        journal.for_target(target_kind="case", target_ref="CASE-001")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        journal.for_target(target_kind=HrEventTargetKind.CASE, target_ref=" ")
