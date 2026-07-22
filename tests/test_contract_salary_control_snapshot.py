from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from application.control.salary_control_snapshot_memory_repository import InMemoryContractSalaryControlSnapshotRepository
from application.control.salary_control_snapshot_use_case import ContractSalaryControlSnapshotFactory, ListContractSalaryControlSnapshotsUseCase, SaveContractSalaryControlSnapshotUseCase
from application.presentation.salary_control_presenter import ContractSalaryControlPaginationViewModel, ContractSalaryControlViewModel, ContractSalaryControlPresentationStatus, ContractSalaryControlRowViewModel
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory
from infrastructure.persistence.contract_salary_control_snapshot_repository import DuplicateContractSalaryControlSnapshotError, SqliteContractSalaryControlSnapshotRepository

SID = UUID("00000000-0000-0000-0000-000000000055")
CID1 = UUID("00000000-0000-0000-0000-000000000001")
CID2 = UUID("00000000-0000-0000-0000-000000000002")
EID = UUID("00000000-0000-0000-0000-000000000101")
NOW = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
REF = date(2026, 7, 1)


def row(contract_id=CID1, status=ContractSalaryControlStatus.COMPLIANT, shortfall=Decimal("0.00")):
    return ContractSalaryControlRowViewModel(
        id=contract_id, contract_id=contract_id, contract_id_label=str(contract_id), employee_id=EID,
        employee_id_label=str(EID), reference_date=REF, reference_date_label="01/07/2026", status=status,
        status_label=status.value, classification_code="G1", classification_code_label="G1",
        remuneration_amount=Decimal("2000.10") if status is not ContractSalaryControlStatus.NOT_EVALUATED else None,
        remuneration_amount_label="", applicable_minimum_amount=Decimal("2100.20") if status is not ContractSalaryControlStatus.NOT_EVALUATED else None,
        applicable_minimum_amount_label="", shortfall_amount=shortfall, shortfall_amount_label="",
        minimum_source=ApplicableSalaryMinimumSource.CCNS if status is not ContractSalaryControlStatus.NOT_EVALUATED else None,
        minimum_source_label="", territory=SmicTerritory.METROPOLITAN_FRANCE if status is not ContractSalaryControlStatus.NOT_EVALUATED else None,
        territory_label="", failure_reason=ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION if status is ContractSalaryControlStatus.NOT_EVALUATED else None,
        failure_reason_label="", failure_message="Classification manquante" if status is ContractSalaryControlStatus.NOT_EVALUATED else None,
        failure_message_label="", issue_code="MINIMUM_SALARY_SHORTFALL" if status is ContractSalaryControlStatus.NON_COMPLIANT else None,
        issue_code_label="", issue_message="Ecart" if status is ContractSalaryControlStatus.NON_COMPLIANT else None, issue_message_label="",
    )


def vm(rows):
    return ContractSalaryControlViewModel(REF, "01/07/2026", tuple(rows), len(rows), sum(r.status is ContractSalaryControlStatus.COMPLIANT for r in rows), sum(r.status is ContractSalaryControlStatus.NON_COMPLIANT for r in rows), sum(r.status is ContractSalaryControlStatus.NOT_EVALUATED for r in rows), len(rows), len(rows), sum((r.shortfall_amount for r in rows), Decimal("0.00")), "", True, True, ContractSalaryControlPresentationStatus.SUCCESS, "", "", ContractSalaryControlPaginationViewModel(0, None, False, False, None, None, 1 if rows else None, len(rows) if rows else None, len(rows), ""), None)


def factory():
    return ContractSalaryControlSnapshotFactory(snapshot_id_factory=lambda: SID, clock=lambda: NOW)


def test_creation_snapshot_vide_immutable():
    snap = factory().from_rows((), reference_date=REF)
    assert snap.total_contracts == 0
    assert snap.rows == ()
    with pytest.raises(FrozenInstanceError):
        snap.total_contracts = 1


def test_creation_conforme_decimal_uuid_date_datetime_enum():
    snap = factory().from_view_model(vm([row()]))
    assert snap.snapshot_id == SID
    assert snap.reference_date == REF
    assert snap.executed_at == NOW
    assert snap.rows[0].remuneration_amount == Decimal("2000.10")
    assert snap.rows[0].status is ContractSalaryControlStatus.COMPLIANT
    assert snap.rows[0].minimum_source is ApplicableSalaryMinimumSource.CCNS


def test_controle_mixte_erreurs_anomalies_ordre_deterministe():
    rows = [row(CID1, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("100.10")), row(CID2, ContractSalaryControlStatus.NOT_EVALUATED)]
    snap = factory().from_view_model(vm(rows))
    assert [r.contract_id for r in snap.rows] == [CID1, CID2]
    assert snap.total_shortfall_amount == Decimal("100.10")
    assert snap.non_compliant_contracts == 1
    assert snap.rows[0].issue_code == "MINIMUM_SALARY_SHORTFALL"
    assert snap.rows[1].failure_reason is ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION


def test_refus_doublons_contract_id_et_incoherence_reference_date():
    with pytest.raises(ValueError):
        factory().from_view_model(vm([row(), row()]))
    other = row(CID2)
    object.__setattr__(other, "reference_date", date(2026, 7, 2))
    with pytest.raises(ValueError):
        factory().from_rows((other,), reference_date=REF)


def test_use_cases_memoire_save_get_list_filtre_doublon_absence_recalcul():
    repo = InMemoryContractSalaryControlSnapshotRepository()
    snap = SaveContractSalaryControlSnapshotUseCase(repo, factory()).execute(vm([row()]))
    assert repo.get(SID) == snap
    assert ListContractSalaryControlSnapshotsUseCase(repo).execute() == (snap,)
    assert ListContractSalaryControlSnapshotsUseCase(repo).execute(reference_date=REF) == (snap,)
    with pytest.raises(Exception):
        repo.save(snap)


def test_repository_sqlite_serialisation_migration_idempotente_transaction_rollback_absence_float(tmp_path):
    repo = SqliteContractSalaryControlSnapshotRepository(tmp_path / "snapshots.sqlite")
    repo.ensure_schema()
    snap = factory().from_view_model(vm([row(CID1, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("10.05"))]))
    saved = repo.save(snap)
    loaded = repo.get(saved.snapshot_id)
    assert loaded == snap
    assert repo.list_all() == (snap,)
    assert repo.list_by_reference_date(REF) == (snap,)
    with pytest.raises(DuplicateContractSalaryControlSnapshotError):
        repo.save(snap)
    import sqlite3
    conn = sqlite3.connect(tmp_path / "snapshots.sqlite")
    assert conn.execute("SELECT total_shortfall_amount FROM tw_contract_salary_control_snapshots").fetchone()[0] == "10.05"
    assert conn.execute("SELECT COUNT(*) FROM tw_contract_salary_control_snapshot_rows").fetchone()[0] == 1
