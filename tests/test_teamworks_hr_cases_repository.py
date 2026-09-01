import sqlite3
from datetime import date, datetime, timezone

import pytest

from domain.hr_connections import (
    ExchangeStatus,
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
from infrastructure.persistence.teamworks_hr_cases_repository import (
    TEAMWORKS_HR_CASES_SCHEMA_VERSION,
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


def _repository(tmp_path):
    path = tmp_path / "teamworks-cases.sqlite"
    return (
        TeamworksHrCasesRepository(db_factory=lambda: LocalGestionDb(path)),
        path,
    )


def _case(
    *,
    case_id="case-1",
    employee_ref="42",
    organization_code="urssaf",
    due_on=date(2026, 9, 10),
):
    return HrCase.create(
        case_id=case_id,
        case_type=HrCaseType.create(code="dpae", label="DPAE"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier=employee_ref,
        ),
        organization_code=organization_code,
        opened_on=date(2026, 9, 1),
        due_on=due_on,
        expected_documents=(
            ExpectedDocument.create(
                code="contrat",
                label="Contrat signé",
                required=True,
            ),
            ExpectedDocument.create(
                code="piece_identite",
                label="Pièce d'identité",
                required=False,
            ),
        ),
        source="embauche",
        comment="Préparation administrative",
    )


def _event(*, event_id="evt-1", target_ref="case-1"):
    return HrAuditEvent.create(
        event_id=event_id,
        kind=HrEventKind.CASE_CREATED,
        target_kind=HrEventTargetKind.CASE,
        target_ref=target_ref,
        occurred_at=datetime(2026, 9, 1, 8, 30, tzinfo=timezone.utc),
        actor_ref="user-1",
        source="teamworks-ui",
        fields=(
            HrAuditField.create(key="status", value="todo"),
            HrAuditField.create(key="organization", value="urssaf"),
        ),
    )


def test_schema_is_additive_versioned_and_indexed(tmp_path):
    repository, path = _repository(tmp_path)

    assert repository.schema_version() == TEAMWORKS_HR_CASES_SCHEMA_VERSION == 1

    with sqlite3.connect(path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tw_hr_%'"
            ).fetchall()
        }
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_tw_hr_%'"
            ).fetchall()
        }
        foreign_keys = []
        for table in (
            "tw_hr_cases",
            "tw_hr_case_expected_documents",
            "tw_hr_audit_events",
            "tw_hr_audit_fields",
        ):
            foreign_keys.extend(conn.execute("PRAGMA foreign_key_list(%s)" % table).fetchall())

    assert {
        "tw_hr_schema_versions",
        "tw_hr_cases",
        "tw_hr_case_expected_documents",
        "tw_hr_audit_events",
        "tw_hr_audit_fields",
    }.issubset(tables)
    assert {
        "idx_tw_hr_cases_status",
        "idx_tw_hr_cases_subject",
        "idx_tw_hr_cases_organization",
        "idx_tw_hr_audit_target",
    }.issubset(indexes)
    assert foreign_keys == []


def test_case_round_trip_update_and_expected_documents(tmp_path):
    repository, _path = _repository(tmp_path)
    original = _case()

    repository.save_case(structure_ref="structure-a", case=original)
    loaded = repository.get_case(structure_ref="structure-a", case_id="case-1")

    assert loaded == original
    assert len(loaded.expected_documents) == 2

    prepared = original.transition_to(
        HrCaseStatus.PREPARED,
        comment="Dossier prêt à transmettre",
    ).with_exchange_status(ExchangeStatus.READY)
    repository.save_case(structure_ref="structure-a", case=prepared)

    reloaded = repository.get_case(structure_ref="structure-a", case_id="case-1")
    assert reloaded == prepared
    assert reloaded.status is HrCaseStatus.PREPARED
    assert reloaded.exchange_status is ExchangeStatus.READY
    assert reloaded.comment == "Dossier prêt à transmettre"


def test_case_listing_is_structure_scoped_and_stably_ordered(tmp_path):
    repository, _path = _repository(tmp_path)
    later = _case(case_id="case-b", employee_ref="2")
    earlier = HrCase.create(
        case_id="case-a",
        case_type=HrCaseType.create(code="mutuelle", label="Affiliation mutuelle"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="1",
        ),
        organization_code="mutuelle",
        opened_on=date(2026, 8, 31),
        due_on=date(2026, 9, 5),
    )

    repository.save_case(structure_ref="structure-a", case=later)
    repository.save_case(structure_ref="structure-a", case=earlier)
    repository.save_case(
        structure_ref="structure-b",
        case=_case(case_id="other", employee_ref="99"),
    )

    assert [item.case_id for item in repository.list_cases(structure_ref="structure-a")] == [
        "case-a",
        "case-b",
    ]
    assert [item.case_id for item in repository.list_cases(structure_ref="structure-b")] == [
        "other"
    ]


def test_append_only_event_round_trip_filters_and_duplicate_refusal(tmp_path):
    repository, _path = _repository(tmp_path)
    first = _event()
    second = HrAuditEvent.create(
        event_id="evt-2",
        kind=HrEventKind.CONNECTOR_CONFIGURATION_CHANGED,
        target_kind=HrEventTargetKind.ORGANIZATION,
        target_ref="urssaf",
        occurred_at=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        actor_ref="user-1",
        source="teamworks-ui",
        fields=(HrAuditField.create(key="portal_count", value="1"),),
    )

    repository.append_event(structure_ref="structure-a", event=first)
    repository.append_event(structure_ref="structure-a", event=second)

    assert repository.get_event(structure_ref="structure-a", event_id="evt-1") == first
    assert repository.get_event(structure_ref="structure-b", event_id="evt-1") is None

    case_events = repository.list_events(
        structure_ref="structure-a",
        target_kind=HrEventTargetKind.CASE,
        target_ref="case-1",
    )
    assert case_events == (first,)
    assert repository.list_events(structure_ref="structure-a") == (first, second)

    with pytest.raises(DuplicateTeamworksHrAuditEventError):
        repository.append_event(structure_ref="structure-a", event=first)

    # Le même identifiant est autorisé dans une autre structure logique.
    repository.append_event(structure_ref="structure-b", event=first)
    assert repository.get_event(structure_ref="structure-b", event_id="evt-1") == first


def test_repository_rejects_empty_structure_and_invalid_objects(tmp_path):
    repository, _path = _repository(tmp_path)

    with pytest.raises(ValueError):
        repository.list_cases(structure_ref="   ")
    with pytest.raises(TypeError):
        repository.save_case(structure_ref="structure-a", case=object())
    with pytest.raises(TypeError):
        repository.append_event(structure_ref="structure-a", event=object())
