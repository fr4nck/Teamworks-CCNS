"""Adaptateurs de persistance Teamworks-CCNS."""

from infrastructure.persistence.contract_salary_control_snapshot_repository import (
    DuplicateContractSalaryControlSnapshotError,
    SqliteContractSalaryControlSnapshotRepository,
)

__all__ = ["DuplicateContractSalaryControlSnapshotError", "SqliteContractSalaryControlSnapshotRepository"]
