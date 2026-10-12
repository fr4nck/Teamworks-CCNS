import sqlite3
from datetime import date, datetime, timezone

import pytest

from domain.hr_connections import (
    ExchangeStatus,
    HrAuditEvent,
    HrAuditField,
    HrCase,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrEventKind,
    HrEventTargetKind,
)
from infrastructure.persistence import (
    DuplicateTeamworksHrAuditEventError,
    StaleTeamworksHrCaseTransitionError,
    TeamworksHrCaseWorkflowRepository,
    TeamworksHrCasesRepository,
)


class LocalGestionDb:
    def __init__(self, path):
        self.isNetwork = False
        self.connexion = sqlite3.connect(path)
        self.cursor = self.connexion.cursor()

    def Commit(self):
        self.connexion.commit()

    def Close(self):
        self.connexion.close()


def _factory(path):
    return lambda: LocalGestionDb(path)


def _case(status=HrCaseStatus.TODO, exchange_status=ExchangeStatus.NOT_APPLICABLE):
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
        exchange_status=exchange_status,
        comment="Initial",
    )


def _event(event_id="evt-1", kind=HrEventKind.CASE_STATUS_CHANGED):
    return HrAuditEvent.create(
        event_id=event_id,
        kind=kind,
        target_kind=HrEventTargetKind.CASE,
        target_ref="case-1",
        occurred_at=datetime(2026, 9, 1, 20, 0, tzinfo=timezone.utc),
        actor_ref="user-1",
        source="teamworks-ui",
        fields=(
            HrAuditField.create(key="from_status", value="todo"),
            HrAuditField.create(key="to_status", value="prepared"),
        ),
    )


def test_atomic_transition_updates_projection_and_appends_event(tmp_path):
    path = tmp_path / "workflow.sqlite"
    factory = _factory(path)
    cases = TeamworksHrCasesRepository(db_factory=factory)
    initial = _case()
    cases.save_case(structure_ref="structure-a", case=initial)
    repository = TeamworksHrCaseWorkflowRepository(db_factory=factory)

    updated = initial.transition_to(
        HrCaseStatus.PREPARED,
        comment="Dossier prêt",
    )
    event = _event()

    persisted = repository.persist_case_transition(
        structure_ref="structure-a",
        expected_status=HrCaseStatus.TODO,
        case=updated,
        event=event,
    )

    assert persisted == updated
    assert cases.get_case(structure_ref="structure-a", case_id="case-1") == updated
    assert cases.get_event(structure_ref="structure-a", event_id="evt-1") == event


def test_stale_status_rolls_back_without_audit_event(tmp_path):
    path = tmp_path / "workflow.sqlite"
    factory = _factory(path)
    cases = TeamworksHrCasesRepository(db_factory=factory)
    cases.save_case(
        structure_ref="structure-a",
        case=_case(status=HrCaseStatus.PREPARED),
    )
    repository = TeamworksHrCaseWorkflowRepository(db_factory=factory)

    attempted = _case(status=HrCaseStatus.CANCELLED)
    with pytest.raises(StaleTeamworksHrCaseTransitionError):
        repository.persist_case_transition(
            structure_ref="structure-a",
            expected_status=HrCaseStatus.TODO,
            case=attempted,
            event=_event(),
        )

    assert cases.get_case(structure_ref="structure-a", case_id="case-1").status is HrCaseStatus.PREPARED
    assert cases.get_event(structure_ref="structure-a", event_id="evt-1") is None


def test_concurrent_exchange_change_is_treated_as_stale(tmp_path):
    path = tmp_path / "workflow.sqlite"
    factory = _factory(path)
    cases = TeamworksHrCasesRepository(db_factory=factory)
    cases.save_case(
        structure_ref="structure-a",
        case=_case(exchange_status=ExchangeStatus.READY),
    )
    repository = TeamworksHrCaseWorkflowRepository(db_factory=factory)

    attempted = _case(status=HrCaseStatus.PREPARED)
    with pytest.raises(StaleTeamworksHrCaseTransitionError):
        repository.persist_case_transition(
            structure_ref="structure-a",
            expected_status=HrCaseStatus.TODO,
            case=attempted,
            event=_event(),
        )

    current = cases.get_case(structure_ref="structure-a", case_id="case-1")
    assert current.status is HrCaseStatus.TODO
    assert current.exchange_status is ExchangeStatus.READY
    assert cases.get_event(structure_ref="structure-a", event_id="evt-1") is None


def test_duplicate_event_refuses_transition_before_update(tmp_path):
    path = tmp_path / "workflow.sqlite"
    factory = _factory(path)
    cases = TeamworksHrCasesRepository(db_factory=factory)
    cases.save_case(structure_ref="structure-a", case=_case())
    event = _event()
    cases.append_event(structure_ref="structure-a", event=event)
    repository = TeamworksHrCaseWorkflowRepository(db_factory=factory)

    with pytest.raises(DuplicateTeamworksHrAuditEventError):
        repository.persist_case_transition(
            structure_ref="structure-a",
            expected_status=HrCaseStatus.TODO,
            case=_case(status=HrCaseStatus.PREPARED),
            event=event,
        )

    assert cases.get_case(structure_ref="structure-a", case_id="case-1").status is HrCaseStatus.TODO


def test_transition_rejects_event_that_does_not_describe_status_change(tmp_path):
    path = tmp_path / "workflow.sqlite"
    factory = _factory(path)
    cases = TeamworksHrCasesRepository(db_factory=factory)
    cases.save_case(structure_ref="structure-a", case=_case())
    repository = TeamworksHrCaseWorkflowRepository(db_factory=factory)

    with pytest.raises(ValueError):
        repository.persist_case_transition(
            structure_ref="structure-a",
            expected_status=HrCaseStatus.TODO,
            case=_case(status=HrCaseStatus.PREPARED),
            event=_event(kind=HrEventKind.CASE_CREATED),
        )
