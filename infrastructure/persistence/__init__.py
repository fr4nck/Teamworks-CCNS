"""Adaptateurs de persistance Teamworks-CCNS."""

from infrastructure.persistence.contract_salary_control_snapshot_repository import (
    DuplicateContractSalaryControlSnapshotError,
    SqliteContractSalaryControlSnapshotRepository,
)
from infrastructure.persistence.hr_connections_repository import (
    DuplicateHrAuditEventError,
    SCHEMA_VERSION as HR_CONNECTIONS_SCHEMA_VERSION,
    SqliteHrConnectionsRepository,
)

__all__ = [
    "DuplicateContractSalaryControlSnapshotError",
    "DuplicateHrAuditEventError",
    "HR_CONNECTIONS_SCHEMA_VERSION",
    "SqliteContractSalaryControlSnapshotRepository",
    "SqliteHrConnectionsRepository",
]
