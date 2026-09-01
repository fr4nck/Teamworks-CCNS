import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

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
from infrastructure.persistence.teamworks_hr_cases_repository import (
    DuplicateTeamworksHrAuditEventError,
    TEAMWORKS_HR_CASES_SCHEMA_VERSION,
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


def _case(case_id="case-1", *, status=HrCaseStatus.TODO, documents=()):
    return HrCase.create(
        case_id=case_id,
        case_type=HrCaseType.create(code="mutuelle_affiliation", label="Affiliation mutuelle"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code="mutuelle-demo",
        opened_on=date(2026, 9, 1),
        due_on=date(2026, 9, 15),
        expected_documents=documents,
        source="teamworks",
    ).transition_to(status) if status is HrCaseStatus.PREPARED else HrCase.create(
        case_id=case_id,
        case_type=HrCaseType.create(code="mutuelle_affiliation", label="Affiliation mutuelle"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code="mutuelle-demo",
        opened_on=date(2026, 9, 1),
        due_on=date(2026, 9, 15),
        expected_documents=documents,
        source="teamworks",
    )


def _event(event_id="event-1", *, target_ref="case-1"):
    return HrAuditEvent.create(
        event_id=event_id,
        kind=HrEventKind.CASE_CREATED,
        target_kind=HrEventTargetKind.CASE,
        target_ref=target_ref,
        occurred_at=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
        actor_ref="user-1",
        source="teamworks",
        fields=(
            HrAuditField.create(key="status", value="todo"),
            HrAuditField.create(key="organization", value="mutuelle-demo"),
        ),
    )


def test_schema_est_idempotent_et_versionne_par_composant(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    repository = TeamworksHrCasesRepository(db_factory=_factory(path))
    repository.ensure_schema()

    assert repository.schema_version() == TEAMWORKS_HR_CASES_SCHEMA_VERSION

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT component, schema_version FROM tw_hr_schema_versions "
            "WHERE component = 'hr_cases_runtime'"
        ).fetchall()
    assert rows == [("hr_cases_runtime", TEAMWORKS_HR_CASES_SCHEMA_VERSION)]


def test_dossier_round_trip_avec_pieces_attendues(tmp_path):
    repository = TeamworksHrCasesRepository(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    )
    case = _case(
        documents=(
            ExpectedDocument.create(code="contrat", label="Contrat"),
            ExpectedDocument.create(
                code="rib",
                label="RIB",
                required=False,
            ),
        )
    )

    repository.save_case(structure_ref="structure-1", case=case)
    loaded = repository.get_case(structure_ref="structure-1", case_id=case.case_id)

    assert loaded == case
    assert {item.code for item in loaded.expected_documents} == {"contrat", "rib"}


def test_mise_a_jour_remplace_les_pieces_sans_dupliquer_le_dossier(tmp_path):
    repository = TeamworksHrCasesRepository(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    )
    original = _case(
        documents=(ExpectedDocument.create(code="contrat", label="Contrat"),)
    )
    repository.save_case(structure_ref="structure-1", case=original)

    prepared = original.transition_to(HrCaseStatus.PREPARED, comment="Dossier préparé")
    prepared = HrCase(
        case_id=prepared.case_id,
        case_type=prepared.case_type,
        subject=prepared.subject,
        organization_code=prepared.organization_code,
        opened_on=prepared.opened_on,
        due_on=prepared.due_on,
        status=prepared.status,
        exchange_status=prepared.exchange_status,
        expected_documents=frozenset(
            {ExpectedDocument.create(code="attestation", label="Attestation")}
        ),
        source=prepared.source,
        result=prepared.result,
        comment=prepared.comment,
    )
    repository.save_case(structure_ref="structure-1", case=prepared)

    loaded = repository.get_case(structure_ref="structure-1", case_id=original.case_id)
    assert loaded == prepared
    assert [item.code for item in loaded.expected_documents] == ["attestation"]

    with sqlite3.connect(tmp_path / "teamworks.sqlite") as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM tw_hr_cases WHERE structure_ref=? AND case_id=?",
            ("structure-1", original.case_id),
        ).fetchone()[0]
    assert count == 1


def test_liste_dossiers_reste_isolee_par_structure(tmp_path):
    repository = TeamworksHrCasesRepository(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    )
    repository.save_case(structure_ref="structure-1", case=_case("case-1"))
    repository.save_case(structure_ref="structure-2", case=_case("case-2"))

    assert [item.case_id for item in repository.list_cases(structure_ref="structure-1")] == [
        "case-1"
    ]
    assert [item.case_id for item in repository.list_cases(structure_ref="structure-2")] == [
        "case-2"
    ]


def test_journal_est_append_only_et_filtrable_par_cible(tmp_path):
    repository = TeamworksHrCasesRepository(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    )
    first = _event("event-1", target_ref="case-1")
    second = _event("event-2", target_ref="case-2")

    repository.append_event(structure_ref="structure-1", event=first)
    repository.append_event(structure_ref="structure-1", event=second)

    assert repository.get_event(structure_ref="structure-1", event_id="event-1") == first
    filtered = repository.list_events(
        structure_ref="structure-1",
        target_kind=HrEventTargetKind.CASE,
        target_ref="case-2",
    )
    assert filtered == (second,)

    with pytest.raises(DuplicateTeamworksHrAuditEventError):
        repository.append_event(structure_ref="structure-1", event=first)


def test_journal_n_ecrase_pas_un_evenement_existant(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    repository = TeamworksHrCasesRepository(db_factory=_factory(path))
    first = _event("event-stable")
    repository.append_event(structure_ref="structure-1", event=first)

    conflicting = HrAuditEvent.create(
        event_id="event-stable",
        kind=HrEventKind.CASE_STATUS_CHANGED,
        target_kind=HrEventTargetKind.CASE,
        target_ref="case-1",
        occurred_at=datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc),
        fields=(HrAuditField.create(key="status", value="prepared"),),
    )
    with pytest.raises(DuplicateTeamworksHrAuditEventError):
        repository.append_event(structure_ref="structure-1", event=conflicting)

    assert repository.get_event(structure_ref="structure-1", event_id="event-stable") == first


def test_adaptateur_production_reste_sqlite_mysql_et_hors_ui_reseau():
    source = Path(
        "infrastructure/persistence/teamworks_hr_cases_repository.py"
    ).read_text(encoding="utf-8")

    assert "isNetwork" in source
    assert 'statement.replace("?", "%s")' in source
    assert 'statement.replace("%s", "?")' in source
    for forbidden in (
        "ON CONFLICT",
        "INSERT OR IGNORE",
        "REPLACE INTO",
        "PRAGMA",
        "import wx",
        "webbrowser",
        "requests",
        "FOREIGN KEY",
        "personnes(",
        "contrats(",
    ):
        assert forbidden not in source
