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

__all__ = [
    "DuplicateContractSalaryControlSnapshotError",
    "DuplicateHrAuditEventError",
    "EMPLOYEE_PROTECTION_SCHEMA_VERSION",
    "HR_CONNECTIONS_SCHEMA_VERSION",
    "SqliteContractSalaryControlSnapshotRepository",
    "SqliteEmployeeProtectionRepository",
    "SqliteHrConnectionsRepository",
]
