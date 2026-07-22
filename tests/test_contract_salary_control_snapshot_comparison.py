from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot_comparison import ContractSalaryControlSnapshotChangeType, compare_contract_salary_control_snapshots
from tests.test_contract_salary_control_snapshot import CID1, CID2, REF, factory, row, vm

CID3 = UUID("00000000-0000-0000-0000-000000000003")


def snapshot(rows, minute=0):
    return factory().__class__(snapshot_id_factory=lambda: UUID(f"00000000-0000-0000-0000-000000000{minute + 100:03d}"), clock=lambda: datetime(2026, 7, 22, 10, minute, tzinfo=timezone.utc)).from_view_model(vm(rows))


def test_comparaison_snapshot_detecte_statuts_presence_et_ecarts_sans_recalcul():
    previous = snapshot([
        row(CID1, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("100.00")),
        row(CID2, ContractSalaryControlStatus.COMPLIANT, Decimal("0.00")),
    ], 1)
    current = snapshot([
        row(CID1, ContractSalaryControlStatus.COMPLIANT, Decimal("0.00")),
        row(CID3, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("25.50")),
    ], 2)

    comparison = compare_contract_salary_control_snapshots(previous, current)

    assert [item.contract_id for item in comparison.rows] == [CID1, CID2, CID3]
    assert [item.change_type for item in comparison.rows] == [
        ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT,
        ContractSalaryControlSnapshotChangeType.MISSING_CONTRACT,
        ContractSalaryControlSnapshotChangeType.NEW_CONTRACT,
    ]
    assert comparison.became_compliant_contracts == 1
    assert comparison.became_non_compliant_contracts == 0
    assert comparison.new_contracts == 1
    assert comparison.missing_contracts == 1
    assert comparison.decreased_shortfall_contracts == 1
    assert comparison.total_shortfall_delta == Decimal("-74.50")


def test_comparaison_snapshot_classe_augmentation_et_baisse_ecart_a_statut_identique():
    previous = snapshot([row(CID1, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("10.00")), row(CID2, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("20.00"))], 3)
    current = snapshot([row(CID1, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("15.00")), row(CID2, ContractSalaryControlStatus.NON_COMPLIANT, Decimal("12.00"))], 4)

    comparison = compare_contract_salary_control_snapshots(previous, current)

    assert [item.change_type for item in comparison.rows] == [
        ContractSalaryControlSnapshotChangeType.SHORTFALL_INCREASED,
        ContractSalaryControlSnapshotChangeType.SHORTFALL_DECREASED,
    ]
    assert comparison.increased_shortfall_contracts == 1
    assert comparison.decreased_shortfall_contracts == 1
    assert comparison.total_shortfall_delta == Decimal("-3.00")


def test_comparaison_refuse_les_objets_non_snapshot():
    with pytest.raises(TypeError):
        compare_contract_salary_control_snapshots(object(), snapshot((), 5))
