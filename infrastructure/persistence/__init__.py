"""Adaptateurs de persistance Teamworks-CCNS."""

from infrastructure.persistence.contract_salary_control_snapshot_repository import (
    DuplicateContractSalaryControlSnapshotError,
    SqliteContractSalaryControlSnapshotRepository,
)
from infrastructure.persistence.employee_protection_repository import (
    EMPLOYEE_PROTECTION_SCHEMA_VERSION,
    SqliteEmployeeProtectionRepository,
)
from infrastructure.persistence.hr_connections_repository import (
    DuplicateHrAuditEventError,
    SCHEMA_VERSION as HR_CONNECTIONS_SCHEMA_VERSION,
    SqliteHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_employee_protection_succession_repository import (
    TeamworksEmployeeProtectionSuccessionRepository,
)
from infrastructure.persistence.teamworks_hr_cases_repository import (
    DuplicateTeamworksHrAuditEventError,
    TEAMWORKS_HR_CASES_SCHEMA_VERSION,
    TeamworksHrCasesRepository,
)
from infrastructure.persistence.teamworks_hr_connections_repository import (
    TEAMWORKS_HR_SCHEMA_VERSION,
    TeamworksHrConnectionsRepository,
)
from infrastructure.persistence.teamworks_structure_identity_repository import (
    TEAMWORKS_STRUCTURE_IDENTITY_SCHEMA_VERSION,
    TeamworksStructureIdentityRepository,
)

__all__ = [
    "DuplicateContractSalaryControlSnapshotError",
    "DuplicateHrAuditEventError",
    "DuplicateTeamworksHrAuditEventError",
    "EMPLOYEE_PROTECTION_SCHEMA_VERSION",
    "HR_CONNECTIONS_SCHEMA_VERSION",
    "TEAMWORKS_HR_CASES_SCHEMA_VERSION",
    "TEAMWORKS_HR_SCHEMA_VERSION",
    "TEAMWORKS_STRUCTURE_IDENTITY_SCHEMA_VERSION",
    "SqliteContractSalaryControlSnapshotRepository",
    "SqliteEmployeeProtectionRepository",
    "SqliteHrConnectionsRepository",
    "TeamworksEmployeeProtectionSuccessionRepository",
    "TeamworksHrCasesRepository",
    "TeamworksHrConnectionsRepository",
    "TeamworksStructureIdentityRepository",
]
