from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone, date
from decimal import Decimal
from uuid import UUID

import pytest

from application.control.salary_control_snapshot_memory_repository import InMemoryContractSalaryControlSnapshotRepository
from application.control.salary_control_snapshot_use_case import CompareContractSalaryControlSnapshotsUseCase, ContractSalaryControlSnapshotNotFoundError
from application.presentation.salary_control_snapshot_comparison_presenter import ContractSalaryControlSnapshotComparisonPresenter
from domain.contracts.contract_salary_control_projection import ContractSalaryControlStatus
from domain.contracts.contract_salary_control_snapshot import ContractSalaryControlSnapshot, ContractSalaryControlSnapshotRow
from domain.contracts.contract_salary_control_snapshot_comparison import ContractSalaryControlSnapshotChangeType, CompareContractSalaryControlSnapshotsService
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason
from domain.convention import ApplicableSalaryMinimumSource

REF = date(2026, 7, 1)
NOW = datetime(2026, 7, 22, 10, tzinfo=timezone.utc)
SID1 = UUID("10000000-0000-0000-0000-000000000001")
SID2 = UUID("10000000-0000-0000-0000-000000000002")
CID1 = UUID("20000000-0000-0000-0000-000000000001")
CID2 = UUID("20000000-0000-0000-0000-000000000002")
CID3 = UUID("20000000-0000-0000-0000-000000000003")
EID = UUID("30000000-0000-0000-0000-000000000001")


def r(cid=CID1, status=ContractSalaryControlStatus.COMPLIANT, remuneration=Decimal("2200.00"), minimum=Decimal("2100.00"), shortfall=Decimal("0.00"), classification="G1", source=ApplicableSalaryMinimumSource.CCNS, issue=None, failure=None):
    if status is ContractSalaryControlStatus.NOT_EVALUATED:
        remuneration = None if remuneration == Decimal("2200.00") else remuneration
        minimum = None if minimum == Decimal("2100.00") else minimum
        source = None if source is ApplicableSalaryMinimumSource.CCNS else source
        failure = failure or ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION
    return ContractSalaryControlSnapshotRow(cid, EID, status, remuneration, minimum, shortfall, classification, source, None, failure, "motif" if failure else None, issue, "anomalie" if issue else None)


def snap(snapshot_id, rows):
    rows = tuple(rows)
    return ContractSalaryControlSnapshot(snapshot_id, REF, NOW, len(rows), sum(x.status is ContractSalaryControlStatus.COMPLIANT for x in rows), sum(x.status is ContractSalaryControlStatus.NON_COMPLIANT for x in rows), sum(x.status is ContractSalaryControlStatus.NOT_EVALUATED for x in rows), sum((x.shortfall_amount for x in rows), Decimal("0.00")), rows)


def compare(before_rows, after_rows):
    return CompareContractSalaryControlSnapshotsService().compare(snap(SID1, before_rows), snap(SID2, after_rows))


def test_identiques_immutabilite_unchanged_decimal_sans_float():
    c = compare([r()], [r()])
    assert c.unchanged is True
    assert c.improved is False and c.degraded is False
    assert c.rows[0].change_type is ContractSalaryControlSnapshotChangeType.UNCHANGED
    assert type(c.total_shortfall_delta) is Decimal
    assert not any(type(v) is float for row in c.rows for v in (row.remuneration_delta, row.minimum_delta, row.shortfall_delta))
    with pytest.raises(FrozenInstanceError):
        c.rows[0].shortfall_delta = Decimal("1.00")


def test_meme_snapshot_id_refuse_et_types_stricts():
    with pytest.raises(ValueError):
        CompareContractSalaryControlSnapshotsService().compare(snap(SID1, [r()]), snap(SID1, [r()]))
    with pytest.raises(TypeError):
        CompareContractSalaryControlSnapshotsService().compare(object(), snap(SID2, []))


@pytest.mark.parametrize("before_status,after_status,change", [
    (ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlSnapshotChangeType.BECAME_COMPLIANT),
    (ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlSnapshotChangeType.BECAME_NON_COMPLIANT),
    (ContractSalaryControlStatus.COMPLIANT, ContractSalaryControlStatus.NOT_EVALUATED, ContractSalaryControlSnapshotChangeType.BECAME_NOT_EVALUATED),
    (ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlStatus.NON_COMPLIANT, ContractSalaryControlSnapshotChangeType.REMAINS_NON_COMPLIANT),
])
def test_types_de_changement_statut(before_status, after_status, change):
    b = r(status=before_status, shortfall=Decimal("5.00") if before_status is ContractSalaryControlStatus.NON_COMPLIANT else Decimal("0.00"))
    a = r(status=after_status, shortfall=Decimal("7.00") if after_status is ContractSalaryControlStatus.NON_COMPLIANT else Decimal("0.00"), issue="MINIMUM_SALARY_SHORTFALL" if after_status is ContractSalaryControlStatus.NON_COMPLIANT else None)
    assert compare([b], [a]).rows[0].change_type is change


def test_nouveau_absent_ordre_deterministe_et_deltas():
    c = compare([r(CID1, shortfall=Decimal("10.00")), r(CID2)], [r(CID2), r(CID3, remuneration=Decimal("100.10"), minimum=Decimal("120.20"), shortfall=Decimal("20.10"))])
    assert [x.contract_id for x in c.rows] == [CID1, CID2, CID3]
    assert c.rows[0].change_type is ContractSalaryControlSnapshotChangeType.REMOVED_CONTRACT
    assert c.rows[2].change_type is ContractSalaryControlSnapshotChangeType.NEW_CONTRACT
    assert c.rows[2].remuneration_delta == Decimal("100.10")
    assert c.rows[2].minimum_delta == Decimal("120.20")
    assert c.new_contracts == 1 and c.removed_contracts == 1 and c.common_contracts == 1


def test_changements_champs_et_ecarts_positifs_negatifs():
    c = compare([r(remuneration=Decimal("2000.00"), minimum=Decimal("2200.00"), shortfall=Decimal("200.00"), classification="G1", source=ApplicableSalaryMinimumSource.CCNS, issue="A")], [r(remuneration=Decimal("2100.00"), minimum=Decimal("2150.00"), shortfall=Decimal("50.00"), classification="G2", source=ApplicableSalaryMinimumSource.SMIC, issue="B")])
    row = c.rows[0]
    assert row.remuneration_delta == Decimal("100.00")
    assert row.minimum_delta == Decimal("-50.00")
    assert row.shortfall_delta == Decimal("-150.00")
    assert row.classification_code_before == "G1" and row.classification_code_after == "G2"
    assert row.minimum_source_before is ApplicableSalaryMinimumSource.CCNS and row.minimum_source_after is ApplicableSalaryMinimumSource.SMIC
    assert row.issue_code_before == "A" and row.issue_code_after == "B"
    assert c.total_shortfall_delta == Decimal("-150.00") and c.improved is True


def test_restant_conforme_non_evaluable_et_motif_non_evaluation_modifie():
    assert compare([r()], [r(remuneration=Decimal("2201.00"))]).rows[0].change_type is ContractSalaryControlSnapshotChangeType.REMAINS_COMPLIANT
    c = compare([r(status=ContractSalaryControlStatus.NOT_EVALUATED, failure=ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION)], [r(status=ContractSalaryControlStatus.NOT_EVALUATED, failure=ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION)])
    assert c.rows[0].failure_reason_before is ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION
    assert c.rows[0].failure_reason_after is ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION
    assert c.rows[0].change_type is ContractSalaryControlSnapshotChangeType.REMAINS_NOT_EVALUATED


def test_compteurs_total_mixed_improved_degraded_priority():
    c = compare([r(CID1, ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00")), r(CID2, ContractSalaryControlStatus.COMPLIANT)], [r(CID1, ContractSalaryControlStatus.COMPLIANT), r(CID2, ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("20.00"), issue="X")])
    assert c.became_compliant == 1 and c.became_non_compliant == 1
    assert c.total_shortfall_delta == Decimal("10.00")
    assert c.improved is True and c.degraded is True and c.unchanged is False


def test_use_case_repository_memoire_snapshot_absent_et_pas_recalcul():
    repo = InMemoryContractSalaryControlSnapshotRepository([snap(SID1, [r()]), snap(SID2, [r(CID2)])])
    c = CompareContractSalaryControlSnapshotsUseCase(repo).execute(SID1, SID2)
    assert c.before_snapshot_id == SID1
    with pytest.raises(ContractSalaryControlSnapshotNotFoundError):
        CompareContractSalaryControlSnapshotsUseCase(repo).execute(UUID("99999999-0000-0000-0000-000000000000"), SID2)


def test_presentation_deterministe_et_filtres_sans_reconstruction():
    c = compare([r(CID1, ContractSalaryControlStatus.NON_COMPLIANT, shortfall=Decimal("10.00")), r(CID2)], [r(CID1), r(CID2), r(CID3)])
    p = ContractSalaryControlSnapshotComparisonPresenter()
    vm = p.present(c)
    assert "Devenus conformes : 1" in vm.summary_lines
    assert vm.rows[0].change_type_label == "Devenu conforme"
    assert len(p.present(c, filter_key=p.FILTER_IMPROVEMENTS).rows) == 1
    assert len(p.present(c, filter_key=p.FILTER_NEW_CONTRACTS).rows) == 1
    assert p.present(c, filter_key=p.FILTER_ALL).rows[0].contract_id_label == str(CID1)
