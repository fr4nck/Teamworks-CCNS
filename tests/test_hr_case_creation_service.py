from datetime import date, datetime, timezone

import pytest

from application.services.hr_connections.hr_case_creation import (
    HrCaseCreationRequest,
    HrCaseCreationService,
)
from domain.hr_connections import (
    ExchangeStatus,
    ExpectedDocument,
    HrCaseStatus,
    HrCaseSubjectKind,
    HrEventKind,
)


class FakeProfiles:
    def __init__(self, known=("urssaf",)):
        self.known = set(known)

    def get_profile(self, *, structure_ref, organization_code):
        if organization_code not in self.known:
            return None
        return object()


class FakeCreationRepository:
    def __init__(self):
        self.cases = {}
        self.events = []

    def get_case(self, *, structure_ref, case_id):
        return self.cases.get((structure_ref, case_id))

    def create_case_with_event(self, *, structure_ref, case, event):
        self.cases[(structure_ref, case.case_id)] = case
        self.events.append((structure_ref, event))
        return case


def _request(**overrides):
    values = dict(
        case_type_code="dpae",
        case_type_label="DPAE",
        subject_kind=HrCaseSubjectKind.PERSON,
        subject_identifier="42",
        organization_code="urssaf",
        opened_on=date(2026, 9, 1),
        due_on=date(2026, 9, 3),
        expected_documents=(
            ExpectedDocument.create(
                code="contrat",
                label="Contrat de travail",
                required=True,
            ),
        ),
        comment="À préparer",
    )
    values.update(overrides)
    return HrCaseCreationRequest(**values)


def _service(repository=None, profiles=None):
    return HrCaseCreationService(
        repository=repository or FakeCreationRepository(),
        profile_repository=profiles or FakeProfiles(),
        now_provider=lambda: datetime(2026, 9, 1, 21, 0, tzinfo=timezone.utc),
        case_id_factory=lambda: "case-1",
        event_id_factory=lambda: "event-1",
    )


def test_create_builds_todo_case_and_append_only_creation_event():
    repository = FakeCreationRepository()
    service = _service(repository=repository)

    result = service.create(
        structure_ref="structure-a",
        request=_request(),
        actor_ref="user-1",
    )

    assert result.case.case_id == "case-1"
    assert result.case.status is HrCaseStatus.TODO
    assert result.case.exchange_status is ExchangeStatus.NOT_APPLICABLE
    assert result.case.organization_code == "urssaf"
    assert result.case.subject.identifier == "42"
    assert result.case.source == "teamworks-ui"
    assert {item.code for item in result.case.expected_documents} == {"contrat"}
    assert result.event.kind is HrEventKind.CASE_CREATED
    assert result.event.target_ref == "case-1"
    assert result.event.actor_ref == "user-1"
    assert dict((field.key, field.value) for field in result.event.fields) == {
        "case_type": "dpae",
        "subject_kind": "person",
        "organization_code": "urssaf",
    }
    assert repository.events == [("structure-a", result.event)]


def test_create_requires_configured_organization_before_any_persistence():
    repository = FakeCreationRepository()
    service = _service(repository=repository, profiles=FakeProfiles(known=()))

    with pytest.raises(LookupError, match="doit être configuré"):
        service.create(structure_ref="structure-a", request=_request())

    assert repository.cases == {}
    assert repository.events == []


def test_create_refuses_generated_case_identifier_collision():
    repository = FakeCreationRepository()
    repository.cases[("structure-a", "case-1")] = object()
    service = _service(repository=repository)

    with pytest.raises(ValueError, match="existe déjà"):
        service.create(structure_ref="structure-a", request=_request())

    assert repository.events == []


def test_creation_timestamp_must_be_timezone_aware():
    service = HrCaseCreationService(
        repository=FakeCreationRepository(),
        profile_repository=FakeProfiles(),
        now_provider=lambda: datetime(2026, 9, 1, 21, 0),
        case_id_factory=lambda: "case-1",
        event_id_factory=lambda: "event-1",
    )

    with pytest.raises(ValueError, match="fuseau"):
        service.create(structure_ref="structure-a", request=_request())


def test_request_rejects_due_date_before_opening():
    with pytest.raises(ValueError, match="ne peut pas précéder"):
        _request(due_on=date(2026, 8, 31))


def test_service_does_not_infer_legal_case_type_or_expected_documents():
    result = _service().create(
        structure_ref="structure-a",
        request=_request(
            case_type_code="custom",
            case_type_label="Démarche libre",
            expected_documents=(),
        ),
    )

    assert result.case.case_type.code == "custom"
    assert result.case.case_type.label == "Démarche libre"
    assert result.case.expected_documents == frozenset()
