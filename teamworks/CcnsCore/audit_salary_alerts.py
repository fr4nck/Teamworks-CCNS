from __future__ import annotations

from application.control import GenerateContractSalaryAlertsUseCase
from infrastructure.persistence import SqliteContractSalaryControlSnapshotRepository


def generate_salary_control_alerts(*, repository=None):
    repo = repository or SqliteContractSalaryControlSnapshotRepository()
    return GenerateContractSalaryAlertsUseCase(repo).execute()
