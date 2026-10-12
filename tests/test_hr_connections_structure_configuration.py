from domain.hr_connections import (
    ConnectionProfile,
    HrOrganization,
    OrganizationKind,
    PortalLink,
)
from application.services.hr_connections import build_reference_connector_registry
from application.services.hr_connections.structure_configuration import (
    StructureHrConnectionsService,
)


class FakeProfileRepository:
    def __init__(self):
        self.items = {}

    def save_profile(self, profile):
        self.items[(profile.structure_ref, profile.organization.code)] = profile
        return profile

    def get_profile(self, *, structure_ref, organization_code):
        return self.items.get((structure_ref, organization_code))

    def list_profiles(self, *, structure_ref):
        return tuple(
            profile
            for (owner, _), profile in sorted(self.items.items())
            if owner == structure_ref
        )


def _profile(*, structure_ref="PMSL", with_portal=True):
    return ConnectionProfile.create(
        structure_ref=structure_ref,
        organization=HrOrganization.create(
            code="urssaf-bretagne",
            label="URSSAF Bretagne",
            kind=OrganizationKind.URSSAF,
        ),
        portal_links=(
            [PortalLink.create(url="https://example.org/urssaf", label="Portail URSSAF")]
            if with_portal
            else []
        ),
    )


def _service(repository=None):
    return StructureHrConnectionsService(
        repository=repository or FakeProfileRepository(),
        registry=build_reference_connector_registry(),
    )


def test_save_profile_returns_ui_agnostic_configuration_projection():
    repository = FakeProfileRepository()
    service = _service(repository)

    view = service.save_profile(_profile())

    assert repository.get_profile(
        structure_ref="PMSL", organization_code="urssaf-bretagne"
    ) == view.profile
    assert view.has_configured_connector
    assert len(view.connectors) == 1
    assert view.connectors[0].connector_id == "urssaf_manual_portal"
    assert view.connectors[0].configured


def test_profile_without_portal_is_persistable_but_exposes_local_configuration_gap():
    service = _service()

    view = service.save_profile(_profile(with_portal=False))

    assert not view.has_configured_connector
    assert not view.connectors[0].configured
    assert view.connectors[0].messages


def test_get_configuration_returns_none_for_unknown_organization():
    service = _service()

    assert service.get_configuration(
        structure_ref="PMSL", organization_code="inconnu"
    ) is None


def test_list_configurations_is_scoped_to_structure():
    repository = FakeProfileRepository()
    service = _service(repository)
    service.save_profile(_profile(structure_ref="PMSL"))
    service.save_profile(_profile(structure_ref="AUTRE"))

    views = service.list_configurations(structure_ref="PMSL")

    assert len(views) == 1
    assert views[0].profile.structure_ref == "PMSL"


def test_connector_options_expose_reference_connector_without_marking_it_configured():
    service = _service()

    options = service.connector_options(organization_kind=OrganizationKind.URSSAF)

    assert len(options) == 1
    assert options[0].connector_id == "urssaf_manual_portal"
    assert not options[0].configured
    assert options[0].messages == ("Profil non encore configuré.",)


def test_unsupported_other_family_has_no_reference_connector_option():
    service = _service()

    assert service.connector_options(organization_kind=OrganizationKind.OTHER) == ()
