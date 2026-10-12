import sqlite3
from datetime import date

import pytest

from application.bootstrap.hr_case_dashboard_factory import HrCaseDashboardRuntimeFactory
from domain.hr_connections import (
    ConnectionProfile,
    EffectivePeriod,
    HrCase,
    HrCaseSubject,
    HrCaseSubjectKind,
    HrCaseType,
    HrOrganization,
    OrganizationKind,
    PortalLink,
)
from infrastructure.persistence.teamworks_hr_cases_repository import TeamworksHrCasesRepository
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


def _db_factory(path):
    return lambda: LocalGestionDb(path)


def test_runtime_builds_dashboard_from_active_teamworks_database(tmp_path):
    path = tmp_path / "teamworks-runtime.sqlite"
    factory = _db_factory(path)
    structure_ref = TeamworksStructureIdentityRepository(
        db_factory=factory
    ).get_or_create_structure_ref()

    profiles = TeamworksHrConnectionsRepository(db_factory=factory)
    profiles.save_profile(
        ConnectionProfile.create(
            structure_ref=structure_ref,
            organization=HrOrganization.create(
                code="urssaf",
                label="URSSAF Bretagne",
                kind=OrganizationKind.URSSAF,
            ),
            portal_links=(
                PortalLink.create(
                    url="https://example.org/urssaf",
                    label="Portail employeur",
                ),
            ),
            effective_period=EffectivePeriod(starts_on=date(2026, 1, 1)),
        )
    )

    cases = TeamworksHrCasesRepository(db_factory=factory)
    cases.save_case(
        structure_ref=structure_ref,
        case=HrCase.create(
            case_id="dpae-42",
            case_type=HrCaseType.create(code="dpae", label="DPAE"),
            subject=HrCaseSubject.create(
                kind=HrCaseSubjectKind.PERSON,
                identifier="42",
            ),
            organization_code="urssaf",
            opened_on=date(2026, 9, 1),
            due_on=date(2026, 9, 2),
        ),
    )

    runtime = HrCaseDashboardRuntimeFactory(db_factory=factory).create()
    dashboard = runtime.build(as_of=date(2026, 9, 3))

    assert dashboard.total_count == 1
    assert dashboard.open_count == 1
    assert dashboard.overdue_count == 1
    assert dashboard.orphan_organization_count == 0
    assert dashboard.rows[0].organization_label == "URSSAF Bretagne"
    assert dashboard.rows[0].subject_identifier == "42"


def test_runtime_keeps_structure_identity_private(tmp_path):
    path = tmp_path / "teamworks-runtime.sqlite"
    runtime = HrCaseDashboardRuntimeFactory(db_factory=_db_factory(path)).create()

    assert not hasattr(runtime, "structure_ref")
    assert hasattr(runtime, "_structure_ref")


def test_runtime_requires_explicit_reference_date(tmp_path):
    path = tmp_path / "teamworks-runtime.sqlite"
    runtime = HrCaseDashboardRuntimeFactory(db_factory=_db_factory(path)).create()

    with pytest.raises(TypeError):
        runtime.build(as_of="2026-09-01")
