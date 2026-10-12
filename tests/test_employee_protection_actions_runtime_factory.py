import sqlite3
from datetime import date
from pathlib import Path

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


def test_actions_runtime_writes_and_closes_record_on_active_teamworks_database(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    db_factory = _factory(path)
    structure_ref = TeamworksStructureIdentityRepository(
        db_factory=db_factory
    ).get_or_create_structure_ref()
    repository = TeamworksHrConnectionsRepository(db_factory=db_factory)
    repository.save_profile(
        ConnectionProfile.create(
            structure_ref=structure_ref,
            organization=HrOrganization.create(
                code="mutuelle-demo",
                label="Mutuelle Démo",
                kind=OrganizationKind.MUTUELLE,
            ),
        )
    )

    runtime = EmployeeProtectionActionsRuntimeFactory(
        db_factory=db_factory,
        record_id_factory=lambda: "record-42",
    ).create()
    created = runtime.register(
        employee_ref="42",
        request=EmployeeProtectionCreateRequest(
            organization_code="mutuelle-demo",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ACTIVE,
            starts_on=date(2026, 9, 1),
            contribution_profile_code="NON_CADRE",
        ),
    ).record

    assert runtime.structure_ref == structure_ref
    assert created.record_id == "record-42"
    assert repository.get_employee_protection(
        structure_ref=structure_ref,
        record_id="record-42",
    ) == created

    ended = runtime.end(
        employee_ref="42",
        record_id="record-42",
        ends_on=date(2026, 12, 31),
    ).record
    persisted = repository.get_employee_protection(
        structure_ref=structure_ref,
        record_id="record-42",
    )

    assert ended.status is EmployeeProtectionStatus.ENDED
    assert persisted == ended
    assert ended.effective_period.starts_on == date(2026, 9, 1)
    assert ended.effective_period.ends_on == date(2026, 12, 31)


def test_actions_runtime_factory_stays_out_of_ui_network_and_secret_storage():
    source = Path(
        "application/bootstrap/employee_protection_actions_factory.py"
    ).read_text(encoding="utf-8")

    for token in (
        "import wx",
        "Dlg.",
        "Ctrl.",
        "webbrowser",
        "requests",
        "SecretStore",
        "password",
        "token",
    ):
        assert token not in source
