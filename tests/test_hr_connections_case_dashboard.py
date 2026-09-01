from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from application.services.hr_connections import HrCaseDashboardService
from domain.hr_connections import (
    ConnectionProfile,
    ExchangeStatus,
    ExpectedDocument,
    HrCase,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrOrganization,
    OrganizationKind,
)


class FakeCaseRepository:
    def __init__(self, cases=()):
        self.cases = tuple(cases)
        self.calls = []

    def list_cases(self, *, structure_ref):
        self.calls.append(structure_ref)
        return self.cases


class FakeProfileRepository:
    def __init__(self, profiles=()):
        self.profiles = tuple(profiles)
        self.calls = []

    def list_profiles(self, *, structure_ref):
        self.calls.append(structure_ref)
        return self.profiles

    def get_profile(self, *, structure_ref, organization_code):
        for profile in self.profiles:
            if (
                profile.structure_ref == structure_ref
                and profile.organization.code == organization_code
            ):
                return profile
        return None

    def save_profile(self, profile):
        raise AssertionError("Le cockpit est en lecture seule.")


def _profile(code="urssaf", label="URSSAF Bretagne"):
    return ConnectionProfile.create(
        structure_ref="structure-1",
        organization=HrOrganization.create(
            code=code,
            label=label,
            kind=OrganizationKind.URSSAF,
        ),
    )


def _case(
    case_id,
    *,
    status=HrCaseStatus.TODO,
    exchange_status=ExchangeStatus.NOT_APPLICABLE,
    due_on=None,
    organization_code="urssaf",
):
    base = HrCase.create(
        case_id=case_id,
        case_type=HrCaseType.create(code="dpae", label="DPAE"),
        subject=HrCaseSubject.create(
            kind=HrCaseSubjectKind.PERSON,
            identifier="42",
        ),
        organization_code=organization_code,
        opened_on=date(2026, 9, 1),
        due_on=due_on,
        expected_documents=(
            ExpectedDocument.create(code="contrat", label="Contrat", required=True),
            ExpectedDocument.create(code="note", label="Note interne", required=False),
        ),
    )
    return replace(base, status=status, exchange_status=exchange_status)


def _service(cases, profiles=(_profile(),)):
    case_repository = FakeCaseRepository(cases)
    profile_repository = FakeProfileRepository(profiles)
    return (
        HrCaseDashboardService(
            case_repository=case_repository,
            profile_repository=profile_repository,
        ),
        case_repository,
        profile_repository,
    )


def test_dashboard_counts_business_and_technical_attention_separately():
    service, _, _ = _service(
        (
            _case("todo"),
            _case("anomaly", status=HrCaseStatus.ANOMALY),
            _case(
                "technical-failure",
                status=HrCaseStatus.SUBMITTED,
                exchange_status=ExchangeStatus.FAILED,
            ),
            _case("accepted", status=HrCaseStatus.ACCEPTED),
        )
    )

    dashboard = service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 10),
    )

    assert dashboard.total_count == 4
    assert dashboard.open_count == 3
    assert dashboard.anomaly_count == 1
    assert dashboard.submitted_count == 1
    assert dashboard.accepted_count == 1
    assert dashboard.exchange_failed_count == 1
    assert dashboard.attention_count == 2

    anomaly = next(row for row in dashboard.rows if row.case_id == "anomaly")
    technical = next(
        row for row in dashboard.rows if row.case_id == "technical-failure"
    )
    assert anomaly.business_attention is True
    assert anomaly.technical_attention is False
    assert technical.business_attention is False
    assert technical.technical_attention is True


def test_dashboard_marks_only_open_past_due_cases_as_overdue():
    service, _, _ = _service(
        (
            _case("late", due_on=date(2026, 9, 5)),
            _case(
                "closed-late",
                status=HrCaseStatus.ACCEPTED,
                due_on=date(2026, 9, 5),
            ),
            _case("today", due_on=date(2026, 9, 10)),
        )
    )

    dashboard = service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 10),
    )

    assert dashboard.overdue_count == 1
    assert next(row for row in dashboard.rows if row.case_id == "late").overdue is True
    assert next(
        row for row in dashboard.rows if row.case_id == "closed-late"
    ).overdue is False
    assert next(row for row in dashboard.rows if row.case_id == "today").overdue is False


def test_dashboard_keeps_orphan_organization_visible_without_inventing_label():
    service, _, _ = _service(
        (_case("orphan", organization_code="ancien-organisme"),)
    )

    dashboard = service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 10),
    )

    row = dashboard.rows[0]
    assert row.organization_code == "ancien-organisme"
    assert row.organization_label is None
    assert row.organization_configured is False
    assert dashboard.orphan_organization_count == 1


def test_dashboard_exposes_expected_document_counts_without_claiming_presence():
    service, _, _ = _service((_case("docs"),))

    row = service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 10),
    ).rows[0]

    assert row.expected_document_count == 2
    assert row.required_document_count == 1
    assert not hasattr(row, "missing_document_count")
    assert not hasattr(row, "documents_complete")


def test_dashboard_sorts_attention_first_then_due_date():
    service, _, _ = _service(
        (
            _case("ordinary", due_on=date(2026, 9, 8)),
            _case("anomaly", status=HrCaseStatus.ANOMALY, due_on=None),
            _case("late", due_on=date(2026, 9, 2)),
        )
    )

    dashboard = service.build(
        structure_ref="structure-1",
        as_of=date(2026, 9, 5),
    )

    assert [row.case_id for row in dashboard.rows] == [
        "late",
        "anomaly",
        "ordinary",
    ]


def test_dashboard_rejects_invalid_reference_date_and_structure():
    service, _, _ = _service(())

    with pytest.raises(ValueError, match="structure"):
        service.build(structure_ref=" ", as_of=date(2026, 9, 1))
    with pytest.raises(TypeError, match="date"):
        service.build(structure_ref="structure-1", as_of="2026-09-01")


def test_dashboard_service_has_no_ui_sql_network_or_legal_claims():
    source = Path(
        "application/services/hr_connections/hr_case_dashboard.py"
    ).read_text(encoding="utf-8").lower()

    for token in (
        "import wx",
        "sqlite3",
        "gestiondb",
        "requests",
        "webbrowser",
        "est conforme",
        "non conforme",
        "obligation légale",
    ):
        assert token not in source
