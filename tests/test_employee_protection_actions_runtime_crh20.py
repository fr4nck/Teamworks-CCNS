import sqlite3
from datetime import date

import pytest

from application.bootstrap.employee_protection_actions_factory import (
    EmployeeProtectionActionsRuntimeFactory,
)
from application.services.hr_connections import EmployeeProtectionCreateRequest
from domain.hr_connections import (
    ConnectionProfile,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    HrOrganization,
    OrganizationKind,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TeamworksStructureIdentityRepository,
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


def _factory(path):
    return lambda: LocalGestionDb(path)


def _save_profile(repository, structure_ref, code, label, kind):
    repository.save_profile(
        ConnectionProfile.create(
            structure_ref=structure_ref,
            organization=HrOrganization.create(
                code=code,
                label=label,
                kind=kind,
            ),
        )
    )


def test_actions_runtime_lists_only_employee_protection_organizations(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    db_factory = _factory(path)
    structure_ref = TeamworksStructureIdentityRepository(
        db_factory=db_factory
    ).get_or_create_structure_ref()
    repository = TeamworksHrConnectionsRepository(db_factory=db_factory)

    _save_profile(
        repository,
        structure_ref,
        "urssaf-demo",
        "Urssaf",
        OrganizationKind.URSSAF,
    )
    _save_profile(
        repository,
        structure_ref,
        "pst35",
        "PST 35",
        OrganizationKind.SPST,
    )
    _save_profile(
        repository,
        structure_ref,
        "mutuelle-demo",
        "Mutuelle Démo",
        OrganizationKind.MUTUELLE,
    )

    runtime = EmployeeProtectionActionsRuntimeFactory(
        db_factory=db_factory,
    ).create()
    options = runtime.available_organizations()

    assert [(option.code, option.kind) for option in options] == [
        ("mutuelle-demo", OrganizationKind.MUTUELLE),
        ("pst35", OrganizationKind.SPST),
    ]


def test_actions_runtime_get_record_checks_employee_boundary(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    db_factory = _factory(path)
    structure_ref = TeamworksStructureIdentityRepository(
        db_factory=db_factory
    ).get_or_create_structure_ref()
    repository = TeamworksHrConnectionsRepository(db_factory=db_factory)
    _save_profile(
        repository,
        structure_ref,
        "mutuelle-demo",
        "Mutuelle Démo",
        OrganizationKind.MUTUELLE,
    )

    runtime = EmployeeProtectionActionsRuntimeFactory(
        db_factory=db_factory,
        record_id_factory=lambda: "record-safe",
    ).create()
    created = runtime.register(
        employee_ref="42",
        request=EmployeeProtectionCreateRequest(
            organization_code="mutuelle-demo",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ACTIVE,
            starts_on=date(2026, 9, 1),
        ),
    ).record

    assert runtime.get_record(
        employee_ref="42",
        record_id=created.record_id,
    ) == created

    with pytest.raises(ValueError, match="n'appartient pas"):
        runtime.get_record(
            employee_ref="99",
            record_id=created.record_id,
        )
