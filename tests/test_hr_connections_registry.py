import pytest

from domain.hr_connections import (
    ConfigurationCheck,
    ConnectionProfile,
    ConnectorCapability,
    ConnectorDescriptor,
    ConnectorMode,
    ConnectorRegistry,
    ConnectorState,
    HrOrganization,
    OrganizationKind,
)


class FakeConnector:
    def __init__(self, descriptor: ConnectorDescriptor) -> None:
        self._descriptor = descriptor
        self.check_calls = 0

    @property
    def descriptor(self) -> ConnectorDescriptor:
        return self._descriptor

    def check_configuration(
        self,
        profile: ConnectionProfile | None,
    ) -> ConfigurationCheck:
        self.check_calls += 1
        if profile is None:
            return ConfigurationCheck.missing("Profil de connexion absent.")
        return ConfigurationCheck.ok()


def _connector(
    connector_id: str,
    *,
    kind: OrganizationKind,
    capabilities: set[ConnectorCapability],
    mode: ConnectorMode,
    state: ConnectorState,
) -> FakeConnector:
    return FakeConnector(
        ConnectorDescriptor.create(
            connector_id=connector_id,
            organization_kinds={kind},
            capabilities=capabilities,
            version="1.0",
            modes={mode},
            state=state,
        )
    )


def test_connector_descriptor_requires_id_version_family_and_mode():
    with pytest.raises(ValueError):
        ConnectorDescriptor.create(
            connector_id=" ",
            organization_kinds={OrganizationKind.URSSAF},
            capabilities=set(),
            version="1.0",
            modes={ConnectorMode.MANUAL},
        )
    with pytest.raises(ValueError):
        ConnectorDescriptor.create(
            connector_id="test",
            organization_kinds=set(),
            capabilities=set(),
            version="1.0",
            modes={ConnectorMode.MANUAL},
        )
    with pytest.raises(ValueError):
        ConnectorDescriptor.create(
            connector_id="test",
            organization_kinds={OrganizationKind.URSSAF},
            capabilities=set(),
            version="1.0",
            modes=set(),
        )


def test_registry_registers_connectors_and_rejects_duplicate_ids():
    connector = _connector(
        "urssaf-manual",
        kind=OrganizationKind.URSSAF,
        capabilities={ConnectorCapability.DEEP_LINK},
        mode=ConnectorMode.MANUAL,
        state=ConnectorState.AVAILABLE,
    )
    registry = ConnectorRegistry([connector])

    assert registry.get("urssaf-manual") is connector
    assert registry.all() == (connector,)

    with pytest.raises(ValueError):
        registry.register(connector)
    with pytest.raises(KeyError):
        registry.get("unknown")


def test_registry_discovers_connectors_by_kind_capability_and_state():
    urssaf = _connector(
        "urssaf-manual",
        kind=OrganizationKind.URSSAF,
        capabilities={ConnectorCapability.DEEP_LINK, ConnectorCapability.MANUAL_STATUS},
        mode=ConnectorMode.MANUAL,
        state=ConnectorState.AVAILABLE,
    )
    net_entreprises = _connector(
        "net-file",
        kind=OrganizationKind.NET_ENTREPRISES,
        capabilities={ConnectorCapability.DOCUMENT_IMPORT, ConnectorCapability.DOCUMENT_EXPORT},
        mode=ConnectorMode.FILE,
        state=ConnectorState.EXPERIMENTAL,
    )
    registry = ConnectorRegistry([net_entreprises, urssaf])

    assert registry.find(organization_kind=OrganizationKind.URSSAF) == (urssaf,)
    assert registry.find(capability=ConnectorCapability.DOCUMENT_IMPORT) == (net_entreprises,)
    assert registry.find(states={ConnectorState.AVAILABLE}) == (urssaf,)
    assert registry.find(
        organization_kind=OrganizationKind.NET_ENTREPRISES,
        capability=ConnectorCapability.DOCUMENT_EXPORT,
        states={ConnectorState.EXPERIMENTAL},
    ) == (net_entreprises,)


def test_registry_does_not_check_configuration_until_explicitly_requested():
    connector = _connector(
        "urssaf-manual",
        kind=OrganizationKind.URSSAF,
        capabilities={ConnectorCapability.DEEP_LINK},
        mode=ConnectorMode.MANUAL,
        state=ConnectorState.NOT_CONFIGURED,
    )
    registry = ConnectorRegistry([connector])

    registry.all()
    registry.find(organization_kind=OrganizationKind.URSSAF)
    assert connector.check_calls == 0

    result = registry.check_configuration("urssaf-manual", None)

    assert connector.check_calls == 1
    assert not result.configured
    assert result.messages == ("Profil de connexion absent.",)


def test_configuration_check_with_profile_is_side_effect_free_contract():
    connector = _connector(
        "mutuelle-manual",
        kind=OrganizationKind.MUTUELLE,
        capabilities={ConnectorCapability.MANUAL_STATUS},
        mode=ConnectorMode.MANUAL,
        state=ConnectorState.AVAILABLE,
    )
    registry = ConnectorRegistry([connector])
    organization = HrOrganization.create(
        code="mutuelle",
        label="Mutuelle",
        kind=OrganizationKind.MUTUELLE,
    )
    profile = ConnectionProfile.create(
        structure_ref="structure-1",
        organization=organization,
        capabilities={ConnectorCapability.MANUAL_STATUS},
    )

    result = registry.check_configuration("mutuelle-manual", profile)

    assert result.configured
    assert result.messages == ()
