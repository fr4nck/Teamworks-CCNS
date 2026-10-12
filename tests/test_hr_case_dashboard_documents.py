from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from application.services.hr_connections import HrCaseDashboardService
from domain.hr_connections import (
    ConnectionProfile,
    ExpectedDocument,
    HrCase,
    HrCaseDocumentReceipt,
    HrCaseDocumentState,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrOrganization,
    OrganizationKind,
)


class FakeCaseRepository:
    def __init__(self, cases):
        self.cases = tuple(cases)

    def list_cases(self, *, structure_ref):
        assert structure_ref == "structure-1"
        return self.cases


class FakeProfileRepository:
    def list_profiles(self, *, structure_ref):
        assert structure_ref == "structure-1"
        return (
            ConnectionProfile.create(
                structure_ref=structure_ref,
                organization=HrOrganization.create(
                    code="urssaf",
                    label="URSSAF Bretagne",
                    kind=OrganizationKind.URSSAF,
                ),
            ),
        )


class FakeDocumentRepository:
    def __init__(self, receipts):
        self.receipts = tuple(receipts)
        self.calls = []

    def list_receipts_for_structure(self, *, structure_ref):
        self.calls.append(structure_ref)
        return self.receipts


def _case(case_id="case-1", *, status=HrCaseStatus.TODO):
    case = HrCase.create(
        case_id=case_id,
        case_type=HrCaseType.create(code="dpae", label="DPAE"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code="urssaf",
        opened_on=date(2026, 9, 1),
        expected_documents=(
            ExpectedDocument.create(code="contrat", label="Contrat", required=True),
            ExpectedDocument.create(code="note", label="Note interne", required=False),
        ),
    )
    return replace(case, status=status)


def _receipt(
    document_code,
    *,
    case_id="case-1",
    state=HrCaseDocumentState.RECEIVED,
):
    return HrCaseDocumentReceipt(
        case_id=case_id,
        document_code=document_code,
        state=state,
        received_on=date(2026, 9, 2),
        withdrawn_on=(
            date(2026, 9, 3)
            if state is HrCaseDocumentState.WITHDRAWN
            else None
        ),
        artifact_ref=None,
        source="test",
    )


def _service(cases, receipts):
    document_repository = FakeDocumentRepository(receipts)
    return (
        HrCaseDashboardService(
            case_repository=FakeCaseRepository(cases),
            profile_repository=FakeProfileRepository(),
            document_repository=document_repository,
        ),
        document_repository,
    )


def test_dashboard_counts_received_and_missing_expected_documents():
    service, repository = _service(
        (_case(),),
        (
            _receipt("contrat"),
            _receipt("note", state=HrCaseDocumentState.WITHDRAWN),
        ),
    )

    dashboard = service.build(structure_ref="structure-1", as_of=date(2026, 9, 5))
    row = dashboard.rows[0]

    assert repository.calls == ["structure-1"]
    assert row.document_tracking_available is True
    assert row.expected_document_count == 2
    assert row.required_document_count == 1
    assert row.received_document_count == 1
    assert row.missing_expected_document_count == 1
    assert row.required_missing_document_count == 0
    assert row.required_document_receipts_complete is True
    assert row.document_attention is False
    assert dashboard.received_document_count == 1
    assert dashboard.required_missing_document_count == 0


def test_missing_required_document_is_administrative_attention_only_for_open_case():
    service, _ = _service((_case(),), (_receipt("note"),))
    dashboard = service.build(structure_ref="structure-1", as_of=date(2026, 9, 5))
    row = dashboard.rows[0]

    assert row.required_missing_document_count == 1
    assert row.required_document_receipts_complete is False
    assert row.document_attention is True
    assert row.business_attention is False
    assert row.technical_attention is False
    assert dashboard.document_attention_count == 1
    assert dashboard.attention_count == 1

    closed_service, _ = _service(
        (_case(status=HrCaseStatus.ACCEPTED),),
        (_receipt("note"),),
    )
    closed = closed_service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 5),
    ).rows[0]
    assert closed.required_missing_document_count == 1
    assert closed.document_attention is False
    assert closed.needs_attention is False


def test_dashboard_keeps_document_presence_unknown_without_tracking_repository():
    service = HrCaseDashboardService(
        case_repository=FakeCaseRepository((_case(),)),
        profile_repository=FakeProfileRepository(),
    )

    row = service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 5),
    ).rows[0]

    assert row.document_tracking_available is False
    assert row.received_document_count is None
    assert row.missing_expected_document_count is None
    assert row.required_missing_document_count is None
    assert row.required_document_receipts_complete is None
    assert row.document_attention is False


def test_unexpected_receipt_is_exposed_as_coherence_attention_without_counting_received():
    service, _ = _service((_case(),), (_receipt("piece-inconnue"),))

    row = service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 5),
    ).rows[0]

    assert row.unexpected_document_receipt_count == 1
    assert row.document_coherence_attention is True
    assert row.received_document_count == 0
    assert row.required_missing_document_count == 1


def test_receipt_for_unknown_case_is_rejected_instead_of_being_silently_attributed():
    service, _ = _service((_case(),), (_receipt("contrat", case_id="other-case"),))

    with pytest.raises(ValueError, match="inconnue"):
        service.build(structure_ref="structure-1", as_of=date(2026, 9, 5))


def test_document_projection_is_grouped_and_read_only_by_contract():
    source = Path(
        "infrastructure/persistence/teamworks_hr_case_dashboard_documents_repository.py"
    ).read_text(encoding="utf-8").lower()

    assert "list_receipts_for_structure" in source
    assert "where structure_ref = ? order by case_id, document_code" in source
    assert "insert into" not in source
    assert "update " not in source
    assert "delete from" not in source
    assert "case_id = ?" not in source


def test_dashboard_factory_composes_the_grouped_document_projection():
    source = Path("application/bootstrap/hr_case_dashboard_factory.py").read_text(
        encoding="utf-8"
    )

    assert "TeamworksHrCaseDashboardDocumentRepository" in source
    assert "document_repository=document_repository" in source
