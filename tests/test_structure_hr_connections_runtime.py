import sqlite3
from datetime import date
from pathlib import Path

from application.bootstrap.structure_hr_connections_factory import (
    StructureHrConnectionsRuntimeFactory,
    StructureOrganizationProfileRequest,
)
from domain.hr_connections import OrganizationKind, OrganizationReference, PortalLink


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


def test_runtime_expose_exactement_les_familles_de_connecteurs_de_reference(tmp_path):
    runtime = StructureHrConnectionsRuntimeFactory(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    ).create()

    assert runtime.supported_kinds() == (
        OrganizationKind.URSSAF,
        OrganizationKind.NET_ENTREPRISES,
        OrganizationKind.MUTUELLE,
        OrganizationKind.PREVOYANCE,
        OrganizationKind.RETRAITE_COMPLEMENTAIRE,
        OrganizationKind.OPCO,
        OrganizationKind.SPST,
        OrganizationKind.FRANCE_TRAVAIL,
    )


def test_runtime_enregistre_un_organisme_et_son_portail_sur_la_base_active(tmp_path):
    runtime = StructureHrConnectionsRuntimeFactory(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    ).create()

    saved = runtime.save_configuration(
        StructureOrganizationProfileRequest(
            code="mutuelle-principale",
            label="Mutuelle Démo",
            kind=OrganizationKind.MUTUELLE,
            references=(
                OrganizationReference.create(
                    reference_type="contrat",
                    value="CONTRAT-42",
                    label="Contrat collectif",
                ),
            ),
            portal_links=(
                PortalLink.create(
                    label="Espace employeur",
                    url="https://example.org/employeur",
                ),
            ),
            starts_on=date(2026, 9, 1),
        )
    )

    assert saved.profile.organization.code == "mutuelle-principale"
    assert saved.has_configured_connector
    assert len(saved.profile.references) == 1
    assert len(saved.profile.portal_links) == 1

    configurations = runtime.list_configurations()
    assert len(configurations) == 1
    assert configurations[0].profile == saved.profile


def test_modification_conserve_le_code_stable_et_remplace_les_collections(tmp_path):
    runtime = StructureHrConnectionsRuntimeFactory(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    ).create()
    runtime.save_configuration(
        StructureOrganizationProfileRequest(
            code="prevoyance",
            label="Prévoyance A",
            kind=OrganizationKind.PREVOYANCE,
            references=(
                OrganizationReference.create(reference_type="contrat", value="A"),
            ),
        )
    )

    updated = runtime.save_configuration(
        StructureOrganizationProfileRequest(
            code="prevoyance",
            label="Prévoyance B",
            kind=OrganizationKind.PREVOYANCE,
            references=(
                OrganizationReference.create(reference_type="contrat", value="B"),
            ),
            portal_links=(
                PortalLink.create(label="Portail", url="https://example.org/prevoyance"),
            ),
        )
    )

    assert updated.profile.organization.code == "prevoyance"
    assert updated.profile.organization.label == "Prévoyance B"
    assert [item.value for item in updated.profile.references] == ["B"]
    assert len(updated.profile.portal_links) == 1


def test_runtime_reste_hors_wxpython_et_du_reseau():
    source = Path(
        "application/bootstrap/structure_hr_connections_factory.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "import wx",
        "webbrowser",
        "requests",
        "urllib.request",
        "SecretStore",
    ):
        assert forbidden not in source
