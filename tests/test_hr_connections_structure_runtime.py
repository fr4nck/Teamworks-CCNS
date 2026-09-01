import sqlite3
from datetime import date
from pathlib import Path

import pytest

from application.bootstrap.hr_connections_structure_factory import (
    StructureHrConnectionsRuntimeFactory,
)
from application.services.hr_connections import StructureConnectionProfileRequest
from domain.hr_connections import (
    ConnectionProfile,
    ConnectorCapability,
    HrOrganization,
    OrganizationKind,
    OrganizationReference,
    PortalLink,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
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


def _db_factory(path):
    return lambda: LocalGestionDb(path)


def _request(*, code="mutuelle-demo", kind=OrganizationKind.MUTUELLE, portal=True):
    return StructureConnectionProfileRequest.create(
        organization_code=code,
        organization_label="Mutuelle Démo",
        organization_kind=kind,
        references=(
            OrganizationReference.create(
                reference_type="contract_number",
                value="CTR-2026",
                label="Contrat collectif",
            ),
        ),
        portal_links=(
            PortalLink.create(
                url="https://example.org/employeur",
                label="Portail employeur",
            ),
        )
        if portal
        else (),
        starts_on=date(2026, 1, 1),
    )


def test_structure_runtime_saves_profile_without_exposing_structure_in_request(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    runtime = StructureHrConnectionsRuntimeFactory(
        db_factory=_db_factory(path),
    ).create()

    request = _request()
    assert "structure_ref" not in request.__dataclass_fields__

    saved = runtime.save_profile(request)
    listed = runtime.list_configurations()

    assert saved.profile.structure_ref == runtime.structure_ref
    assert saved.profile.organization.code == "mutuelle-demo"
    assert saved.profile.references[0].value == "CTR-2026"
    assert saved.profile.portal_links[0].url == "https://example.org/employeur"
    assert len(listed) == 1
    assert listed[0].profile == saved.profile
    assert listed[0].has_configured_connector is True


def test_structure_runtime_reports_manual_connector_unconfigured_without_portal(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    runtime = StructureHrConnectionsRuntimeFactory(
        db_factory=_db_factory(path),
    ).create()

    saved = runtime.save_profile(_request(portal=False))

    assert saved.connectors
    assert saved.has_configured_connector is False
    assert all(item.configured is False for item in saved.connectors)


def test_structure_runtime_preserves_previously_qualified_capabilities_on_edit(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    db_factory = _db_factory(path)
    runtime = StructureHrConnectionsRuntimeFactory(db_factory=db_factory).create()
    repository = TeamworksHrConnectionsRepository(db_factory=db_factory)
    repository.save_profile(
        ConnectionProfile.create(
            structure_ref=runtime.structure_ref,
            organization=HrOrganization.create(
                code="mutuelle-demo",
                label="Ancien libellé",
                kind=OrganizationKind.MUTUELLE,
            ),
            capabilities=(ConnectorCapability.DOCUMENT_EXPORT,),
        )
    )

    saved = runtime.save_profile(_request())

    assert saved.profile.organization.label == "Mutuelle Démo"
    assert saved.profile.capabilities == frozenset(
        {ConnectorCapability.DOCUMENT_EXPORT}
    )


def test_structure_runtime_refuses_kind_change_for_existing_organization(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    runtime = StructureHrConnectionsRuntimeFactory(
        db_factory=_db_factory(path),
    ).create()
    runtime.save_profile(_request())

    with pytest.raises(ValueError, match="famille"):
        runtime.save_profile(
            _request(kind=OrganizationKind.PREVOYANCE)
        )


def test_structure_runtime_does_not_provide_profile_delete_operation():
    runtime_public = {
        name
        for name in dir(
            __import__(
                "application.bootstrap.hr_connections_structure_factory",
                fromlist=["StructureHrConnectionsRuntime"],
            ).StructureHrConnectionsRuntime
        )
        if not name.startswith("_")
    }

    assert "delete_profile" not in runtime_public
    assert "remove_profile" not in runtime_public
    assert "save_profile" in runtime_public


def test_structure_runtime_factory_stays_out_of_wx_network_and_secret_storage():
    source = Path(
        "application/bootstrap/hr_connections_structure_factory.py"
    ).read_text(encoding="utf-8")

    for token in (
        "import wx",
        "webbrowser",
        "requests",
        "SecretStore",
        "password",
        "access_token",
    ):
        assert token not in source
