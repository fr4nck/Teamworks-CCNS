from decimal import Decimal
from tests.test_contract_salary_control_snapshot import row, vm, factory, REF
from application.control.salary_control_snapshot_memory_repository import InMemoryContractSalaryControlSnapshotRepository
from application.control.salary_control_snapshot_use_case import SaveContractSalaryControlSnapshotUseCase
from teamworks.CcnsCore.audit_salary_history import salary_rows_from_audit_rows, save_salary_control_snapshot_from_audit_rows


def test_action_enregistrement_utilise_audit_complet_avant_filtre_sans_controleur():
    rows = [{"salary_control_row": row()}, {"salary_control_row": row(contract_id=__import__('uuid').UUID('00000000-0000-0000-0000-000000000002'))}]
    assert len(salary_rows_from_audit_rows(rows)) == 2


def test_audit_vide():
    try:
        save_salary_control_snapshot_from_audit_rows([], repository=InMemoryContractSalaryControlSnapshotRepository())
    except ValueError as exc:
        assert "Aucun contrôle" in str(exc)
    else:
        raise AssertionError("audit vide accepté")
