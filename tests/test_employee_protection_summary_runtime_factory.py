import sqlite3
from datetime import date
from pathlib import Path
from uuid import UUID

from application.bootstrap.employee_protection_summary_factory import (
    EmployeeProtectionSummaryRuntimeFactory,
)
from domain.hr_connections import (
    ConnectionProfile,
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    HrOrganization,
    OrganizationKind,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TEAMWORKS_STRUCTURE_IDENTITY_SCHEMA_VERSION,
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


def test_structure_identity_is_stable_non_secret_and_stored_once(tmp_path):
    path = tmp_path / "teamworks.sqlite"
    db_factory = _factory(path)

    first = TeamworksStructureIdentityRepository(db_factory=db_factory)
    ref1 = first.get_or_create_structure_ref()
    ref2 = TeamworksStructureIdentityRepository(
        db_factory=db_factory
    ).get_or_create_structure_ref()

    assert ref1 == ref2
    assert str(UUID(ref1)) == ref1

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT singleton_id, structure_ref, schema_version "
            "FROM tw_hr_structure_identity"
        ).fetchall()
    assert rows == [(1, ref1, TEAMWORKS_STRUCTURE_IDENTITY_SCHEMA_VERSION)]


def test_runtime_factory_uses_active_database_identity_and_builds_summary(tmp_path):
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
    repository.save_employee_protection(
        EmployeeProtectionRecord.create(
            record_id="record-42",
            structure_ref=structure_ref,
            employee_ref="42",
            organization_code="mutuelle-demo",
            organization_kind=OrganizationKind.MUTUELLE,
            relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
            status=EmployeeProtectionStatus.ACTIVE,
            effective_period=EffectivePeriod(starts_on=date(2026, 9, 1)),
            contribution_profile_code="NON_CADRE",
        )
    )

    runtime = EmployeeProtectionSummaryRuntimeFactory(
        db_factory=db_factory
    ).create()
    summary = runtime.build(employee_ref="42", as_of=date(2026, 9, 1))

    assert runtime.structure_ref == structure_ref
    assert summary.structure_ref == structure_ref
    assert summary.employee_ref == "42"
    assert summary.total_count == 1
    assert summary.effective_count == 1
    assert summary.payroll_relevant_count == 1


def test_runtime_rejects_empty_employee_reference(tmp_path):
    runtime = EmployeeProtectionSummaryRuntimeFactory(
        db_factory=_factory(tmp_path / "teamworks.sqlite")
    ).create()

    try:
        runtime.build(employee_ref="  ", as_of=date(2026, 9, 1))
    except ValueError as exc:
        assert "salarié" in str(exc)
    else:
        raise AssertionError("Une référence salarié vide doit être refusée.")


def test_structure_identity_does_not_derive_from_connection_configuration():
    source = Path(
        "infrastructure/persistence/teamworks_structure_identity_repository.py"
    ).read_text(encoding="utf-8")

    forbidden = (
        "GetNomFichierDefaut",
        "GetParamConnexionReseau",
        "UTILS_Config",
        "nomFichier",
        "[RESEAU]",
    )
    for token in forbidden:
        assert token not in source


def test_composition_layer_stays_out_of_wxpython_and_historical_ui():
    source = Path(
        "application/bootstrap/employee_protection_summary_factory.py"
    ).read_text(encoding="utf-8")

    for token in (
        "import wx",
        "Dlg.",
        "Ctrl.",
        "DLG_Fiche_individuelle",
        "webbrowser",
        "requests",
    ):
        assert token not in source
