from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from application.control import GenerateContractSalaryAlertsUseCase, InMemoryContractSalaryControlSnapshotRepository, ContractSalaryControlSnapshotNotFoundError
from application.presentation import ContractSalaryAlertPresenter
from domain.contracts import (
    ContractSalaryAlertSeverity,
    ContractSalaryAlertType,
    ContractSalaryControlSnapshot,
    ContractSalaryControlSnapshotRow,
    ContractSalaryControlStatus,
    GenerateContractSalaryAlertsService,
)
from domain.contracts.contract_salary_control_issue_history import TrackContractSalaryControlIssuesService
from domain.contracts.contract_salary_control_snapshot_comparison import CompareContractSalaryControlSnapshotsService

C1 = UUID("10000000-0000-0000-0000-000000000001")
C2 = UUID("10000000-0000-0000-0000-000000000002")
E1 = UUID("20000000-0000-0000-0000-000000000001")


def row(cid=C1, *, status=ContractSalaryControlStatus.COMPLIANT, remuneration=Decimal("120.00"), minimum=Decimal("100.00"), shortfall=Decimal("0.00"), issue_code=None):
    return ContractSalaryControlSnapshotRow(cid, E1, status, remuneration, minimum, shortfall, "G1", None, None, None, None, issue_code, "Anomalie" if issue_code else None)


def snapshot(rows, *, day=1, sid=None):
    rows = tuple(rows)
    return ContractSalaryControlSnapshot(sid or uuid4(), date(2026, 1, day), datetime(2026, 1, day, 8), len(rows), sum(r.status is ContractSalaryControlStatus.COMPLIANT for r in rows), sum(r.status is ContractSalaryControlStatus.NON_COMPLIANT for r in rows), sum(r.status is ContractSalaryControlStatus.NOT_EVALUATED for r in rows), sum((r.shortfall_amount for r in rows), Decimal("0.00")), rows)


def alerts(before, after):
    comparison = CompareContractSalaryControlSnapshotsService().compare(before, after)
    history = TrackContractSalaryControlIssuesService().track(before, after)
    return GenerateContractSalaryAlertsService().generate(after, comparison, history)


def test_aucune_alerte_et_immutabilite():
    collection = alerts(snapshot([row()]), snapshot([row()], day=2))
    assert collection.alerts == ()
    with pytest.raises(FrozenInstanceError):
        collection.alerts = ()


def test_nouvelle_anomalie_persistante_resolue_et_non_conformite():
    before = snapshot([row(C1, status=ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00"), issue_code="min")])
    after = snapshot([row(C1, status=ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("15.00"), issue_code="min"), row(C2, status=ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("5.00"), issue_code="new")], day=2)
    collection = alerts(before, after)
    assert any(a.alert_type is ContractSalaryAlertType.PERSISTENT_ANOMALY and a.severity is ContractSalaryAlertSeverity.CRITICAL for a in collection.alerts)
    assert any(a.alert_type is ContractSalaryAlertType.NEW_ANOMALY and a.severity is ContractSalaryAlertSeverity.WARNING for a in collection.alerts)
    assert any(a.alert_type is ContractSalaryAlertType.NON_COMPLIANT_CONTRACT and a.severity is ContractSalaryAlertSeverity.CRITICAL for a in collection.alerts)
    resolved = alerts(after, snapshot([row(C1), row(C2)], day=3))
    assert any(a.summary_key == "resolved_anomaly" and a.severity is ContractSalaryAlertSeverity.INFO for a in resolved.alerts)
    assert any(a.summary_key == "contract_became_compliant" for a in resolved.alerts)


def test_contrat_non_evalue_hausse_minimum_baisse_remuneration_nouveau_supprime():
    before = snapshot([row(C1, remuneration=Decimal("120.00"), minimum=Decimal("100.00")), row(C2)])
    after = snapshot([row(C1, status=ContractSalaryControlStatus.NOT_EVALUATED, remuneration=Decimal("110.00"), minimum=Decimal("130.00"), issue_code="not_eval")], day=2)
    collection = alerts(before, after)
    assert any(a.alert_type is ContractSalaryAlertType.NOT_EVALUATED_CONTRACT for a in collection.alerts)
    assert any(a.alert_type is ContractSalaryAlertType.MINIMUM_INCREASE for a in collection.alerts)
    assert any(a.alert_type is ContractSalaryAlertType.SALARY_DECREASE for a in collection.alerts)
    assert any(a.alert_type is ContractSalaryAlertType.REMOVED_CONTRACT for a in collection.alerts)
    new_ok = alerts(snapshot([], day=1), snapshot([row(C1)], day=2))
    assert any(a.alert_type is ContractSalaryAlertType.NEW_CONTRACT and a.severity is ContractSalaryAlertSeverity.INFO for a in new_ok.alerts)


def test_ordre_deterministe_presentateur_repository_absent_et_aucun_acces_base():
    before = snapshot([row(C2), row(C1)])
    after = snapshot([row(C2, status=ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("1.00"), issue_code="b"), row(C1, status=ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("1.00"), issue_code="a")], day=2)
    repo = InMemoryContractSalaryControlSnapshotRepository([before, after])
    collection = GenerateContractSalaryAlertsUseCase(repo).execute()
    assert collection.alerts == GenerateContractSalaryAlertsUseCase(repo).execute().alerts
    vm = ContractSalaryAlertPresenter().present(collection, filter_key=ContractSalaryAlertPresenter.FILTER_CRITICAL)
    assert vm.critical_count >= 2
    assert all(row.severity_label == "Critique" for row in vm.rows)
    with pytest.raises(ContractSalaryControlSnapshotNotFoundError):
        GenerateContractSalaryAlertsUseCase(InMemoryContractSalaryControlSnapshotRepository([before])).execute()
