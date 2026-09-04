import sqlite3
from datetime import date, datetime, timezone

import pytest

from domain.hr_connections import (
    ExpectedDocument,
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
from infrastructure.persistence.teamworks_hr_case_creation_repository import (
    DuplicateTeamworksHrCaseError,
    TeamworksHrCaseCreationRepository,
)
from infrastructure.persistence.teamworks_hr_cases_repository import (
    DuplicateTeamworksHrAuditEventError,
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


def _case(case_id="case-1", status=HrCaseStatus.TODO):
    return HrCase(
        case_id=case_id,
        case_type=HrCaseType.create(code="dpae", label="DPAE"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code="urssaf",
        opened_on=date(2026, 9, 1),
        due_on=date(2026, 9, 3),
        status=status,
        expected_documents=frozenset(
            {
                ExpectedDocument.create(
                    code="contrat",
                    label="Contrat de travail",
                    required=True,
                )
            }
        ),
        source="teamworks-ui",
        comment="Initial",
    )


def _event(event_id="event-1", target_ref="case-1", kind=HrEventKind.CASE_CREATED):
    return HrAuditEvent.create(
        event_id=event_id,
        kind=kind,
        target_kind=HrEventTargetKind.CASE,
        target_ref=target_ref,
        occurred_at=datetime(2026, 9, 1, 21, 0, tzinfo=timezone.utc),
        actor_ref="user-1",
        source="teamworks-ui",
        fields=(
            HrAuditField.create(key="case_type", value="dpae"),
            HrAuditField.create(key="subject_kind", value="person"),
            HrAuditField.create(key="organization_code", value="urssaf"),
        ),
    )


def test_atomic_creation_persists_case_documents_and_event(tmp_path):
    path = tmp_path / "creation.sqlite"
    factory = _factory(path)
    repository = TeamworksHrCaseCreationRepository(db_factory=factory)
    reader = TeamworksHrCasesRepository(db_factory=factory)

    case = _case()
    event = _event()
    persisted = repository.create_case_with_event(
        structure_ref="structure-a",
        case=case,
        event=event,
    )

    assert persisted == case
    assert reader.get_case(structure_ref="structure-a", case_id="case-1") == case
    assert reader.get_event(structure_ref="structure-a", event_id="event-1") == event


def test_duplicate_case_refuses_creation_without_second_event(tmp_path):
    path = tmp_path / "creation.sqlite"
    factory = _factory(path)
    repository = TeamworksHrCaseCreationRepository(db_factory=factory)
    reader = TeamworksHrCasesRepository(db_factory=factory)

    repository.create_case_with_event(
        structure_ref="structure-a",
        case=_case(),
        event=_event(),
    )

    with pytest.raises(DuplicateTeamworksHrCaseError):
        repository.create_case_with_event(
            structure_ref="structure-a",
            case=_case(),
            event=_event(event_id="event-2"),
        )

    assert len(reader.list_events(structure_ref="structure-a")) == 1


def test_duplicate_event_rolls_back_case_insert(tmp_path):
    path = tmp_path / "creation.sqlite"
    factory = _factory(path)
    reader = TeamworksHrCasesRepository(db_factory=factory)
    existing_event = _event(event_id="event-1", target_ref="other-case")
    reader.append_event(structure_ref="structure-a", event=existing_event)
    repository = TeamworksHrCaseCreationRepository(db_factory=factory)

    with pytest.raises(DuplicateTeamworksHrAuditEventError):
        repository.create_case_with_event(
            structure_ref="structure-a",
            case=_case(),
            event=_event(event_id="event-1"),
        )

    assert reader.get_case(structure_ref="structure-a", case_id="case-1") is None
    assert reader.get_event(structure_ref="structure-a", event_id="event-1") == existing_event


def test_invalid_event_target_is_rejected_before_persistence(tmp_path):
    path = tmp_path / "creation.sqlite"
    factory = _factory(path)
    repository = TeamworksHrCaseCreationRepository(db_factory=factory)
    reader = TeamworksHrCasesRepository(db_factory=factory)

    with pytest.raises(ValueError, match="ne cible pas"):
        repository.create_case_with_event(
            structure_ref="structure-a",
            case=_case(),
            event=_event(target_ref="other-case"),
        )

    assert reader.get_case(structure_ref="structure-a", case_id="case-1") is None


def test_new_case_must_start_in_todo_state(tmp_path):
    path = tmp_path / "creation.sqlite"
    repository = TeamworksHrCaseCreationRepository(db_factory=_factory(path))

    with pytest.raises(ValueError, match="À faire"):
        repository.create_case_with_event(
            structure_ref="structure-a",
            case=_case(status=HrCaseStatus.PREPARED),
            event=_event(),
        )


def test_creation_adapter_uses_existing_schema_without_new_version(tmp_path):
    path = tmp_path / "creation.sqlite"
    factory = _factory(path)
    cases = TeamworksHrCasesRepository(db_factory=factory)
    version = cases.schema_version()

    TeamworksHrCaseCreationRepository(db_factory=factory)

    assert cases.schema_version() == version
