import sqlite3
from datetime import date, datetime, timezone

import pytest

from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    EffectivePeriod,
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
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)
from infrastructure.persistence.hr_connections_repository import (
    DuplicateHrAuditEventError,
    SCHEMA_VERSION,
    SqliteHrConnectionsRepository,
)


def _repo(tmp_path):
    return SqliteHrConnectionsRepository(tmp_path / "hr-connections.sqlite")


def _profile(*, structure_ref="PMSL"):
    return ConnectionProfile.create(
        structure_ref=structure_ref,
        organization=HrOrganization.create(
            code="mutuelle-demo",
            label="Mutuelle Démo",
            kind=OrganizationKind.MUTUELLE,
        ),
        capabilities=(ConnectorCapability.DEEP_LINK, ConnectorCapability.MANUAL_STATUS),
        references=(
            OrganizationReference.create(
                reference_type="contract_number",
                value="CTR-001",
                label="Contrat collectif",
            ),
        ),
        portal_links=(
            PortalLink.create(url="https://example.org/employeur", label="Portail employeur"),
        ),
        effective_period=EffectivePeriod(
            starts_on=date(2026, 1, 1),
            ends_on=date(2026, 12, 31),
        ),
    )


def _case(*, status=HrCaseStatus.TODO, exchange_status=ExchangeStatus.NOT_APPLICABLE):
    return HrCase(
        case_id="CASE-001",
        case_type=HrCaseType.create(code="mutuelle_affiliation", label="Affiliation mutuelle"),
        subject=HrCaseSubject.create(kind=HrCaseSubjectKind.PERSON, identifier="42"),
        organization_code="mutuelle-demo",
        opened_on=date(2026, 9, 1),
        due_on=date(2026, 9, 10),
        status=status,
        exchange_status=exchange_status,
        expected_documents=frozenset(
            {
                ExpectedDocument.create(code="bulletin", label="Bulletin d'adhésion"),
                ExpectedDocument.create(
                    code="optionnel",
                    label="Justificatif optionnel",
                    required=False,
                ),
            }
        ),
        source="embauche",
        comment="À préparer",
    )


def _event(*, event_id="EVT-001", target_ref="CASE-001"):
    return HrAuditEvent.create(
        event_id=event_id,
        kind=HrEventKind.CASE_STATUS_CHANGED,
        target_kind=HrEventTargetKind.CASE,
        target_ref=target_ref,
        occurred_at=datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc),
        actor_ref="direction",
        source="manual_portal",
        fields=(
            HrAuditField.create(key="previous_status", value="prepared"),
            HrAuditField.create(key="new_status", value="submitted"),
        ),
    )


def test_schema_is_idempotent_and_versioned(tmp_path):
    path = tmp_path / "hr-connections.sqlite"
    repo = SqliteHrConnectionsRepository(path)
    repo.ensure_schema()

    assert repo.schema_version() == SCHEMA_VERSION == 1
    with sqlite3.connect(path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tw_hr_%'"
            ).fetchall()
        }
    assert "tw_hr_connection_profiles" in tables
    assert "tw_hr_cases" in tables
    assert "tw_hr_audit_events" in tables


def test_profile_round_trip_preserves_non_secret_configuration(tmp_path):
    repo = _repo(tmp_path)
    profile = _profile()

    repo.save_profile(profile)
    loaded = repo.get_profile(structure_ref="PMSL", organization_code="mutuelle-demo")

    assert loaded == profile


def test_profile_update_replaces_child_collections_without_duplicates(tmp_path):
    repo = _repo(tmp_path)
    repo.save_profile(_profile())
    updated = ConnectionProfile.create(
        structure_ref="PMSL",
        organization=HrOrganization.create(
            code="mutuelle-demo",
            label="Mutuelle Démo 2027",
            kind=OrganizationKind.MUTUELLE,
        ),
        capabilities=(ConnectorCapability.DEEP_LINK,),
        references=(OrganizationReference.create(reference_type="contract_number", value="CTR-002"),),
        portal_links=(PortalLink.create(url="https://example.org/new", label="Nouveau portail"),),
    )

    repo.save_profile(updated)
    loaded = repo.get_profile(structure_ref="PMSL", organization_code="mutuelle-demo")

    assert loaded == updated
    assert len(repo.list_profiles(structure_ref="PMSL")) == 1


def test_profiles_are_isolated_by_structure(tmp_path):
    repo = _repo(tmp_path)
    repo.save_profile(_profile(structure_ref="PMSL"))
    repo.save_profile(_profile(structure_ref="AUTRE"))

    assert len(repo.list_profiles(structure_ref="PMSL")) == 1
    assert len(repo.list_profiles(structure_ref="AUTRE")) == 1


def test_case_round_trip_preserves_business_and_exchange_status(tmp_path):
    repo = _repo(tmp_path)
    case = _case(status=HrCaseStatus.SUBMITTED, exchange_status=ExchangeStatus.SUCCEEDED)

    repo.save_case(structure_ref="PMSL", case=case)
    loaded = repo.get_case(structure_ref="PMSL", case_id="CASE-001")

    assert loaded == case


def test_case_save_updates_current_projection_without_duplicate_documents(tmp_path):
    repo = _repo(tmp_path)
    original = _case(status=HrCaseStatus.TODO)
    prepared = original.transition_to(HrCaseStatus.PREPARED, comment="Prêt")

    repo.save_case(structure_ref="PMSL", case=original)
    repo.save_case(structure_ref="PMSL", case=prepared)

    loaded = repo.get_case(structure_ref="PMSL", case_id="CASE-001")
    assert loaded == prepared
    assert len(loaded.expected_documents) == 2
    assert len(repo.list_cases(structure_ref="PMSL")) == 1


def test_cases_are_isolated_by_structure_even_with_same_case_id(tmp_path):
    repo = _repo(tmp_path)
    repo.save_case(structure_ref="PMSL", case=_case())
    repo.save_case(structure_ref="AUTRE", case=_case())

    assert len(repo.list_cases(structure_ref="PMSL")) == 1
    assert len(repo.list_cases(structure_ref="AUTRE")) == 1


def test_audit_event_round_trip_filter_and_duplicate_guard(tmp_path):
    repo = _repo(tmp_path)
    first = _event(event_id="EVT-001", target_ref="CASE-001")
    second = _event(event_id="EVT-002", target_ref="CASE-002")

    repo.append_event(structure_ref="PMSL", event=first)
    repo.append_event(structure_ref="PMSL", event=second)

    assert repo.get_event(structure_ref="PMSL", event_id="EVT-001") == first
    assert repo.list_events(
        structure_ref="PMSL",
        target_kind=HrEventTargetKind.CASE,
        target_ref="CASE-001",
    ) == (first,)
    with pytest.raises(DuplicateHrAuditEventError):
        repo.append_event(structure_ref="PMSL", event=first)


def test_same_event_id_can_exist_in_two_structures(tmp_path):
    repo = _repo(tmp_path)
    event = _event()

    repo.append_event(structure_ref="PMSL", event=event)
    repo.append_event(structure_ref="AUTRE", event=event)

    assert repo.get_event(structure_ref="PMSL", event_id="EVT-001") == event
    assert repo.get_event(structure_ref="AUTRE", event_id="EVT-001") == event


def test_repository_rejects_empty_structure_reference(tmp_path):
    repo = _repo(tmp_path)

    with pytest.raises(ValueError):
        repo.save_case(structure_ref=" ", case=_case())
    with pytest.raises(ValueError):
        repo.append_event(structure_ref=" ", event=_event())
