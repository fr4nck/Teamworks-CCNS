import sqlite3
from datetime import datetime, timezone

from application.bootstrap.hr_case_history_factory import HrCaseHistoryRuntimeFactory
from domain.hr_connections import (
    HrAuditEvent,
    HrAuditField,
    HrEventKind,
    HrEventTargetKind,
)
from infrastructure.persistence.teamworks_hr_cases_repository import TeamworksHrCasesRepository
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
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


def test_runtime_reads_case_history_from_active_database(tmp_path):
    path = tmp_path / "history.sqlite"
    factory = _factory(path)
    structure_ref = TeamworksStructureIdentityRepository(
        db_factory=factory
    ).get_or_create_structure_ref()
    repository = TeamworksHrCasesRepository(db_factory=factory)
    repository.append_event(
        structure_ref=structure_ref,
        event=HrAuditEvent.create(
            event_id="evt-1",
            kind=HrEventKind.CASE_STATUS_CHANGED,
            target_kind=HrEventTargetKind.CASE,
            target_ref="case-1",
            occurred_at=datetime(2026, 9, 1, 20, 30, tzinfo=timezone.utc),
            actor_ref="user-1",
            source="teamworks-ui",
            fields=(
                HrAuditField.create(key="from_status", value="todo"),
                HrAuditField.create(key="to_status", value="prepared"),
            ),
        ),
    )

    runtime = HrCaseHistoryRuntimeFactory(db_factory=factory).create()
    history = runtime.build(case_id="case-1")

    assert history.total_count == 1
    assert history.rows[0].event_id == "evt-1"
    assert history.status_change_count == 1


def test_runtime_keeps_structure_identity_private(tmp_path):
    runtime = HrCaseHistoryRuntimeFactory(db_factory=_factory(tmp_path / "empty.sqlite")).create()

    assert not hasattr(runtime, "structure_ref")
    assert hasattr(runtime, "_structure_ref")
