import sqlite3
from datetime import date, datetime, timezone

from application.bootstrap import HrCaseDocumentTrackingRuntimeFactory
from application.services.hr_connections import HrCaseHistoryService
from domain.hr_connections import (
    ExpectedDocument,
    HrCase,
    HrCaseDocumentState,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrEventKind,
)
from infrastructure.persistence import (
    TeamworksHrCasesRepository,
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


def test_runtime_tracks_expected_document_on_active_structure_and_case_history(tmp_path):
    path = tmp_path / "runtime.sqlite"
    db_factory = _factory(path)
    structure_ref = TeamworksStructureIdentityRepository(
        db_factory=db_factory,
    ).get_or_create_structure_ref()
    cases = TeamworksHrCasesRepository(db_factory=db_factory)
    cases.save_case(
        structure_ref=structure_ref,
        case=HrCase(
            case_id="case-1",
            case_type=HrCaseType.create(code="administratif", label="Suivi administratif"),
            subject=HrCaseSubject.create(
                kind=HrCaseSubjectKind.PERSON,
                identifier="42",
            ),
            organization_code="organisme-a",
            opened_on=date(2026, 9, 1),
            expected_documents=frozenset(
                {
                    ExpectedDocument.create(
                        code="justificatif",
                        label="Justificatif",
                        required=True,
                    )
                }
            ),
        ),
    )

    runtime = HrCaseDocumentTrackingRuntimeFactory(
        db_factory=db_factory,
        now_provider=lambda: datetime(2026, 9, 2, 8, 30, tzinfo=timezone.utc),
        event_id_factory=lambda: "evt-doc-runtime",
    ).create()

    before = runtime.build_checklist(case_id="case-1")
    assert before.required_missing_count == 1

    result = runtime.record_received(
        case_id="case-1",
        document_code="justificatif",
        received_on=date(2026, 9, 2),
        artifact_ref="document-17",
        actor_ref="user-1",
    )
    assert result.receipt.state is HrCaseDocumentState.RECEIVED

    after = runtime.build_checklist(case_id="case-1")
    assert after.received_count == 1
    assert after.required_missing_count == 0
    assert after.complete_administratively is True

    history = HrCaseHistoryService(repository=cases).build(
        structure_ref=structure_ref,
        case_id="case-1",
    )
    assert [row.kind for row in history.rows] == [HrEventKind.DOCUMENT_ADDED]
    assert history.rows[0].fields[0].key == "document_code"
