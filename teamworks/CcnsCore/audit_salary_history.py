#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date

from application.control import ContractSalaryControlSnapshotFactory, SaveContractSalaryControlSnapshotUseCase, ListContractSalaryControlSnapshotsUseCase
from application.presentation import ContractSalaryControlRowViewModel
from infrastructure.persistence import SqliteContractSalaryControlSnapshotRepository


def salary_rows_from_audit_rows(rows):
    salary_rows = []
    for row in rows:
        salary_row = row.get("salary_control_row") if isinstance(row, dict) else getattr(row, "salary_control_row", None)
        if salary_row is None:
            continue
        if type(salary_row) is not ContractSalaryControlRowViewModel:
            raise TypeError("salary_control_row doit être un ContractSalaryControlRowViewModel strict.")
        salary_rows.append(salary_row)
    return tuple(salary_rows)


def save_salary_control_snapshot_from_audit_rows(rows, *, repository=None, created_by=None):
    salary_rows = salary_rows_from_audit_rows(rows)
    if not salary_rows:
        raise ValueError("Aucun contrôle salarial complet n'est disponible pour l'enregistrement.")
    reference_date = salary_rows[0].reference_date
    snapshot = ContractSalaryControlSnapshotFactory().from_rows(salary_rows, reference_date=reference_date, created_by=created_by)
    repo = repository or SqliteContractSalaryControlSnapshotRepository()
    return repo.save(snapshot)


def list_salary_control_snapshots(*, repository=None, reference_date: date | None = None):
    repo = repository or SqliteContractSalaryControlSnapshotRepository()
    return ListContractSalaryControlSnapshotsUseCase(repo).execute(reference_date=reference_date)


def compare_salary_control_snapshots(before_snapshot_id, after_snapshot_id, *, repository=None):
    from application.control import CompareContractSalaryControlSnapshotsUseCase
    repo = repository or SqliteContractSalaryControlSnapshotRepository()
    return CompareContractSalaryControlSnapshotsUseCase(repo).execute(before_snapshot_id, after_snapshot_id)


def track_salary_control_issues(before_snapshot_id, after_snapshot_id, *, repository=None):
    from application.control import TrackContractSalaryControlIssuesUseCase
    repo = repository or SqliteContractSalaryControlSnapshotRepository()
    return TrackContractSalaryControlIssuesUseCase(repo).execute(before_snapshot_id, after_snapshot_id)
