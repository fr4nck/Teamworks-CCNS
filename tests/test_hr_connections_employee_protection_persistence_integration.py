from datetime import date

from application.services.hr_connections import EmployeeProtectionService
from domain.hr_connections import (
    ConnectionProfile,
    EffectivePeriod,
    EmployeeProtectionRecord,
    EmployeeProtectionRelationKind,
    EmployeeProtectionStatus,
    HrOrganization,
    OrganizationKind,
)
from infrastructure.persistence import (
    SqliteEmployeeProtectionRepository,
    SqliteHrConnectionsRepository,
)


def test_employee_protection_service_uses_real_reference_repositories(tmp_path):
    profile_repository = SqliteHrConnectionsRepository(tmp_path / "hr-connections.sqlite")
    employee_repository = SqliteEmployeeProtectionRepository(
        tmp_path / "employee-protection.sqlite"
    )
    profile_repository.save_profile(
        ConnectionProfile.create(
            structure_ref="PMSL",
            organization=HrOrganization.create(
                code="unimutuelle",
                label="Unimutuelle",
                kind=OrganizationKind.MUTUELLE,
            ),
        )
    )
    service = EmployeeProtectionService(
        repository=employee_repository,
        profile_repository=profile_repository,
    )
    record = EmployeeProtectionRecord.create(
        record_id="MUT-001",
        structure_ref="PMSL",
        employee_ref="42",
        organization_code="unimutuelle",
        organization_kind=OrganizationKind.MUTUELLE,
        relation_kind=EmployeeProtectionRelationKind.AFFILIATION,
        status=EmployeeProtectionStatus.ACTIVE,
        effective_period=EffectivePeriod(starts_on=date(2026, 9, 1)),
        contribution_profile_code="non_cadre",
    )

    saved = service.save(record)
    loaded = service.get(structure_ref="PMSL", record_id="MUT-001")

    assert saved.record == record
    assert loaded is not None
    assert loaded.record == record
    assert loaded.organization_configured
    assert loaded.organization_label == "Unimutuelle"
    assert service.payroll_relevant_on(
        structure_ref="PMSL",
        employee_ref="42",
        as_of=date(2026, 9, 1),
    ) == (loaded,)
