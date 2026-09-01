from datetime import date, datetime, timezone

import pytest

from application.services.hr_connections import ManualPortalConnector
from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    ConnectorMode,
    ConnectorState,
    ExpectedDocument,
    HrCase,
    HrCaseStatus,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)


def _profile(*, kind: OrganizationKind = OrganizationKind.MUTUELLE, with_portal: bool = True):
    organization = HrOrganization.create(
        code="mutuelle-demo",
        label="Mutuelle Démo",
        kind=kind,
    )
    return ConnectionProfile.create(
        structure_ref="PMSL",
        organization=organization,
        references=[
            OrganizationReference.create(
                reference_type="contract_number",
                value="CTR-2026-001",
                label="Contrat collectif",
            )
        ],
        portal_links=(
            [PortalLink.create(url="https://example.org/employeur", label="Espace employeur")]
            if with_portal
            else []
        ),
    )


def _case(*, status: HrCaseStatus = HrCaseStatus.TODO) -> HrCase:
    case = HrCase.create(
        case_id="CASE-001",
        case_type=HrCaseType.create(code="mutuelle_affiliation", label="Affiliation mutuelle"),
        subject=HrCaseSubject.create(kind=HrCaseSubjectKind.PERSON, identifier="42"),
        organization_code="mutuelle-demo",
        opened_on=date(2026, 9, 1),
        expected_documents=[
            ExpectedDocument.create(code="bulletin", label="Bulletin d'adhésion"),
            ExpectedDocument.create(
                code="justificatif_optionnel",
                label="Justificatif optionnel",
                required=False,
            ),
        ],
    )
    if status is HrCaseStatus.TODO:
        return case
    if status is HrCaseStatus.PREPARED:
        return case.transition_to(HrCaseStatus.PREPARED)
    if status is HrCaseStatus.SUBMITTED:
        return case.transition_to(HrCaseStatus.PREPARED).transition_to(HrCaseStatus.SUBMITTED)
    raise AssertionError("Statut de fixture non pris en charge")


def test_manual_connector_announces_only_manual_fallback_capabilities():
    connector = ManualPortalConnector()

    assert connector.descriptor.state is ConnectorState.AVAILABLE
    assert connector.descriptor.modes == frozenset({ConnectorMode.MANUAL})
    assert connector.descriptor.capabilities == frozenset(
        {ConnectorCapability.DEEP_LINK, ConnectorCapability.MANUAL_STATUS}
    )
    assert ConnectorCapability.API not in connector.descriptor.capabilities
    assert ConnectorCapability.SUBMISSION not in connector.descriptor.capabilities


def test_configuration_requires_a_profile_and_a_configured_portal():
    connector = ManualPortalConnector()

    missing_profile = connector.check_configuration(None)
    assert not missing_profile.configured

    missing_portal = connector.check_configuration(_profile(with_portal=False))
    assert not missing_portal.configured

    assert connector.check_configuration(_profile()).configured


def test_configuration_rejects_an_organization_family_outside_connector_scope():
    connector = ManualPortalConnector(organization_kinds=(OrganizationKind.URSSAF,))

    check = connector.check_configuration(_profile(kind=OrganizationKind.MUTUELLE))

    assert not check.configured


def test_prepare_case_collects_links_references_and_expected_documents_without_side_effect():
    connector = ManualPortalConnector()
    case = _case()
    profile = _profile()

    plan = connector.prepare_case(case=case, profile=profile)

    assert plan.connector_id == "manual_portal"
    assert plan.case_id == "CASE-001"
    assert plan.organization_code == "mutuelle-demo"
    assert plan.portal_links[0].url == "https://example.org/employeur"
    assert plan.references[0].value == "CTR-2026-001"
    assert [item.code for item in plan.required_documents] == ["bulletin"]
    assert [item.code for item in plan.optional_documents] == ["justificatif_optionnel"]
    assert case.status is HrCaseStatus.TODO


def test_prepare_case_refuses_mismatched_organization():
    connector = ManualPortalConnector()
    profile = _profile()
    case = HrCase.create(
        case_id="CASE-OTHER",
        case_type=HrCaseType.create(code="dpae", label="DPAE"),
        subject=HrCaseSubject.create(kind=HrCaseSubjectKind.PERSON, identifier="42"),
        organization_code="urssaf",
        opened_on=date(2026, 9, 1),
    )

    with pytest.raises(ValueError):
        connector.prepare_case(case=case, profile=profile)


def test_portal_open_request_requires_explicit_user_confirmation_and_does_not_open_anything():
    connector = ManualPortalConnector()
    profile = _profile()

    with pytest.raises(PermissionError):
        connector.request_portal_open(profile=profile, user_confirmed=False)

    request = connector.request_portal_open(profile=profile, user_confirmed=True)

    assert request.connector_id == "manual_portal"
    assert request.organization_code == "mutuelle-demo"
    assert request.portal_link.url == "https://example.org/employeur"


def test_portal_open_request_rejects_invalid_portal_index():
    connector = ManualPortalConnector()
    profile = _profile()

    with pytest.raises(TypeError):
        connector.request_portal_open(
            profile=profile,
            user_confirmed=True,
            portal_index=True,
        )
    with pytest.raises(IndexError):
        connector.request_portal_open(
            profile=profile,
            user_confirmed=True,
            portal_index=9,
        )


def test_manual_status_update_is_explicit_audited_and_keeps_previous_case_immutable():
    connector = ManualPortalConnector()
    case = _case(status=HrCaseStatus.PREPARED)

    update = connector.record_manual_status(
        case=case,
        new_status=HrCaseStatus.SUBMITTED,
        event_id="EVT-PORTAL-001",
        occurred_at=datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc),
        actor_ref="direction",
        external_reference="DOSSIER-4587",
        comment="Déposé manuellement sur le portail",
    )

    assert case.status is HrCaseStatus.PREPARED
    assert update.updated_case.status is HrCaseStatus.SUBMITTED
    assert update.updated_case.comment == "Déposé manuellement sur le portail"
    assert update.external_reference == "DOSSIER-4587"
    assert update.audit_event.target_ref == "CASE-001"
    assert update.audit_event.source == "manual_portal"
    fields = {item.key: item.value for item in update.audit_event.fields}
    assert fields == {
        "previous_status": "prepared",
        "new_status": "submitted",
        "external_reference": "DOSSIER-4587",
    }


def test_manual_connector_never_bypasses_case_workflow_or_infers_acceptance():
    connector = ManualPortalConnector()
    case = _case()

    with pytest.raises(ValueError):
        connector.record_manual_status(
            case=case,
            new_status=HrCaseStatus.ACCEPTED,
            event_id="EVT-INVALID",
            occurred_at=datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc),
            actor_ref="direction",
        )


def test_manual_status_update_requires_identified_actor():
    connector = ManualPortalConnector()

    with pytest.raises(ValueError):
        connector.record_manual_status(
            case=_case(status=HrCaseStatus.PREPARED),
            new_status=HrCaseStatus.SUBMITTED,
            event_id="EVT-INVALID",
            occurred_at=datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc),
            actor_ref=" ",
        )
