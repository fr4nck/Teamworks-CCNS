from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from application.control import InMemoryContractSalaryControlSnapshotRepository, TrackContractSalaryControlIssuesUseCase, ContractSalaryControlSnapshotNotFoundError
from domain.contracts import (
    ContractSalaryControlIssueStatus,
    ContractSalaryControlIssueEvolutionType,
    ContractSalaryControlSnapshot,
    ContractSalaryControlSnapshotRow,
    ContractSalaryControlStatus,
    TrackContractSalaryControlIssuesService,
)
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason


def row(contract_id, *, employee_id=None, status=ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00"), issue_code="minimum_shortfall", failure_reason=None, issue_message="Écart"):
    return ContractSalaryControlSnapshotRow(contract_id, employee_id, status, Decimal("100.00"), Decimal("110.00"), shortfall, "G1", None, None, failure_reason, None, issue_code, issue_message)


def snapshot(rows, *, sid=None, day=1):
    rows = tuple(rows)
    return ContractSalaryControlSnapshot(
        sid or uuid4(), date(2026, 1, day), datetime(2026, 1, day, 8), len(rows),
        sum(1 for r in rows if r.status is ContractSalaryControlStatus.COMPLIANT),
        sum(1 for r in rows if r.status is ContractSalaryControlStatus.NON_COMPLIANT),
        sum(1 for r in rows if r.status is ContractSalaryControlStatus.NOT_EVALUATED),
        sum((r.shortfall_amount for r in rows), Decimal("0.00")), rows,
    )


def track(before, after):
    return TrackContractSalaryControlIssuesService().track(before, after)


def test_aucune_anomalie():
    cid = uuid4()
    compliant = row(cid, status=ContractSalaryControlStatus.COMPLIANT, shortfall=Decimal("0.00"), issue_code=None, issue_message=None)
    history = track(snapshot([compliant]), snapshot([compliant], day=2))
    assert history.total_issues == 0
    assert history.rows == ()


def test_nouvelle_anomalie_et_decimal_inchange():
    cid = uuid4()
    history = track(snapshot([], day=1), snapshot([row(cid, shortfall=Decimal("12.34"))], day=2))
    assert history.new_issues == 1
    assert history.rows[0].status is ContractSalaryControlIssueStatus.NEW
    assert history.rows[0].shortfall_amount_after == Decimal("12.34")


def test_anomalie_resolue():
    cid = uuid4()
    history = track(snapshot([row(cid)]), snapshot([], day=2))
    assert history.resolved_issues == 1
    assert history.rows[0].evolution_type is ContractSalaryControlIssueEvolutionType.RESOLVED


def test_anomalie_persistante():
    cid = uuid4()
    history = track(snapshot([row(cid)]), snapshot([row(cid)], day=2))
    assert history.ongoing_issues == 1
    assert history.rows[0].evolution_type is ContractSalaryControlIssueEvolutionType.ONGOING


def test_changement_de_motif_remplace_anomalie():
    cid = uuid4()
    old = row(cid, status=ContractSalaryControlStatus.NOT_EVALUATED, issue_code=None, failure_reason=ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION)
    new = row(cid, status=ContractSalaryControlStatus.NOT_EVALUATED, issue_code=None, failure_reason=ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION)
    history = track(snapshot([old]), snapshot([new], day=2))
    assert {r.status for r in history.rows} == {ContractSalaryControlIssueStatus.NEW, ContractSalaryControlIssueStatus.RESOLVED}
    assert all(r.evolution_type is ContractSalaryControlIssueEvolutionType.REPLACED for r in history.rows)


def test_changement_de_statut():
    cid = uuid4()
    history = track(snapshot([row(cid)]), snapshot([row(cid, status=ContractSalaryControlStatus.NOT_EVALUATED)], day=2))
    assert any(r.evolution_type is ContractSalaryControlIssueEvolutionType.STATUS_CHANGED for r in history.rows)


def test_plusieurs_anomalies_contrats_et_ordre_deterministe():
    c1 = UUID("00000000-0000-0000-0000-000000000002")
    c2 = UUID("00000000-0000-0000-0000-000000000001")
    history = track(snapshot([row(c1, issue_code="b"), row(c2, issue_code="a")]), snapshot([row(c1, issue_code="b"), row(c2, issue_code="a")], day=2))
    assert [r.contract_id for r in history.rows] == [c2, c1]


def test_immutabilite():
    cid = uuid4()
    history = track(snapshot([], day=1), snapshot([row(cid)], day=2))
    with pytest.raises(FrozenInstanceError):
        history.rows[0].issue_code_after = "x"


def test_repository_memoire_snapshots_absents_et_aucun_recalcul():
    before = snapshot([row(uuid4())])
    after = snapshot([], day=2)
    repo = InMemoryContractSalaryControlSnapshotRepository([before, after])
    history = TrackContractSalaryControlIssuesUseCase(repo).execute(before.snapshot_id, after.snapshot_id)
    assert history.resolved_issues == 1
    with pytest.raises(ContractSalaryControlSnapshotNotFoundError):
        TrackContractSalaryControlIssuesUseCase(repo).execute(uuid4(), after.snapshot_id)
