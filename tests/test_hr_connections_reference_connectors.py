import pytest

from application.services.hr_connections import (
    ReferenceManualConnectorSpec,
    build_reference_connector_registry,
    build_reference_manual_connectors,
    reference_manual_connector_specs,
)
from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    ConnectorMode,
    ConnectorState,
    HrOrganization,
    OrganizationKind,
    PortalLink,
)


EXPECTED_KINDS = {
    OrganizationKind.URSSAF,
    OrganizationKind.NET_ENTREPRISES,
    OrganizationKind.MUTUELLE,
    OrganizationKind.PREVOYANCE,
    OrganizationKind.RETRAITE_COMPLEMENTAIRE,
    OrganizationKind.OPCO,
    OrganizationKind.SPST,
    OrganizationKind.FRANCE_TRAVAIL,
}


def test_reference_catalog_covers_expected_organization_families_once():
    specs = reference_manual_connector_specs()

    assert len(specs) == 8
    assert {spec.organization_kind for spec in specs} == EXPECTED_KINDS
    assert len({spec.connector_id for spec in specs}) == len(specs)
    assert OrganizationKind.OTHER not in {spec.organization_kind for spec in specs}


def test_reference_spec_rejects_unknown_generic_family():
    with pytest.raises(ValueError):
        ReferenceManualConnectorSpec(
            connector_id="other_manual_portal",
            label="Autre",
            organization_kind=OrganizationKind.OTHER,
        )


def test_reference_connectors_announce_only_manual_capabilities():
    connectors = build_reference_manual_connectors()

    assert len(connectors) == 8
    for connector in connectors:
        descriptor = connector.descriptor
        assert descriptor.state is ConnectorState.AVAILABLE
        assert descriptor.modes == frozenset({ConnectorMode.MANUAL})
        assert descriptor.capabilities == frozenset(
            {ConnectorCapability.DEEP_LINK, ConnectorCapability.MANUAL_STATUS}
        )
        assert ConnectorCapability.API not in descriptor.capabilities
        assert ConnectorCapability.SUBMISSION not in descriptor.capabilities
        assert ConnectorCapability.STATUS_SYNC not in descriptor.capabilities
        assert len(descriptor.organization_kinds) == 1


def test_reference_registry_registers_all_connectors_without_collision():
    registry = build_reference_connector_registry()

    connectors = registry.all()
    assert len(connectors) == 8
    assert {connector.descriptor.connector_id for connector in connectors} == {
        "urssaf_manual_portal",
        "net_entreprises_manual_portal",
        "mutuelle_manual_portal",
        "prevoyance_manual_portal",
        "retraite_complementaire_manual_portal",
        "opco_manual_portal",
        "spst_manual_portal",
        "france_travail_manual_portal",
    }


def test_registry_can_discover_reference_connector_by_organization_kind():
    registry = build_reference_connector_registry()

    matches = registry.find(organization_kind=OrganizationKind.URSSAF)

    assert len(matches) == 1
    assert matches[0].descriptor.connector_id == "urssaf_manual_portal"


def test_reference_connector_configuration_still_requires_matching_profile_and_portal():
    registry = build_reference_connector_registry()
    connector = registry.get("urssaf_manual_portal")
    organization = HrOrganization.create(
        code="urssaf-bretagne",
        label="URSSAF Bretagne",
        kind=OrganizationKind.URSSAF,
    )

    missing_portal_profile = ConnectionProfile.create(
        structure_ref="PMSL",
        organization=organization,
    )
    assert not connector.check_configuration(missing_portal_profile).configured

    configured_profile = ConnectionProfile.create(
        structure_ref="PMSL",
        organization=organization,
        portal_links=[
            PortalLink.create(
                url="https://example.org/urssaf",
                label="Portail URSSAF",
            )
        ],
    )
    assert connector.check_configuration(configured_profile).configured


def test_reference_connector_rejects_profile_from_another_family():
    registry = build_reference_connector_registry()
    connector = registry.get("urssaf_manual_portal")
    mutuelle_profile = ConnectionProfile.create(
        structure_ref="PMSL",
        organization=HrOrganization.create(
            code="mutuelle-demo",
            label="Mutuelle Démo",
            kind=OrganizationKind.MUTUELLE,
        ),
        portal_links=[
            PortalLink.create(url="https://example.org/mutuelle", label="Portail mutuelle")
        ],
    )

    check = connector.check_configuration(mutuelle_profile)

    assert not check.configured
