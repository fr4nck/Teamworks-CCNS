"""SORTIE-002 — persistance MySQL/MariaDB réelle de ContractTermination."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from domain.employment.termination import (
    CheckState,
    ContractTermination,
    HrInputChecks,
    NoticeStatus,
    TerminationReason,
    TerminationWorkflowStatus,
)
from domain.employment.termination_repository import (
    ActiveTerminationExists,
    TerminationAlreadyExists,
    TerminationNotFound,
    TerminationPersistenceError,
    TerminationVersionConflict,
)
from infrastructure.persistence.mysql_termination_repository import MySqlContractTerminationRepository
from tests.termination_mysql_support import ROOT, termination_db, termination_mysql_server  # noqa: F401

READY_CHECKS = HrInputChecks(
    hours=CheckState.NONE,
    absences=CheckState.PROVIDED,
    leave=CheckState.PROVIDED,
    variable_pay=CheckState.NONE,
    exceptional_items=CheckState.NONE,
)


def make_termination(contract_id="contract-1", **overrides) -> ContractTermination:
    values = dict(
        contract_id=contract_id,
        effective_end_date=date(2026, 10, 31),
        last_worked_date=date(2026, 10, 30),
        known_at=datetime(2026, 10, 1, 9, 30, 15, 123456, tzinfo=timezone.utc),
        created_at=datetime(2026, 10, 2, 8, 0, 0, 999999, tzinfo=timezone.utc),
        created_by="director-1",
        decision_date=date(2026, 9, 28),
        termination_reason=TerminationReason.END_OF_FIXED_TERM,
        notification_date=date(2026, 9, 29),
        notice_status=NoticeStatus.PROVIDED,
        notice_start=date(2026, 10, 1),
        notice_end=date(2026, 10, 31),
        comments="Fin de CDD — heures déjà saisies",
        hr_checks=READY_CHECKS,
    )
    values.update(overrides)
    return ContractTermination(**values)


def stored_row(connect, termination_id):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT version, workflow_status, active_contract_id, comments, effective_end_date"
            " FROM tw_contract_termination WHERE termination_id = %s",
            (termination_id,),
        )
        return cur.fetchone()
    finally:
        conn.close()


def count_rows(connect):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tw_contract_termination")
        return cur.fetchone()[0]
    finally:
        conn.close()


def test_add_then_get_roundtrips_every_field(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)

    loaded = repository.get(termination.termination_id)
    assert loaded == termination
    assert loaded.version == termination.version == 1
    assert loaded.known_at == datetime(2026, 10, 1, 9, 30, 15, tzinfo=timezone.utc)
    assert loaded.known_at.tzinfo is timezone.utc
    assert loaded.termination_reason is TerminationReason.END_OF_FIXED_TERM
    assert loaded.hr_checks.absences is CheckState.PROVIDED
    assert loaded.hr_checks.hours is CheckState.NONE
    assert loaded.comments == "Fin de CDD — heures déjà saisies"


def test_unknown_states_survive_storage_and_still_block_ready(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination(
        termination_reason=TerminationReason.UNKNOWN,
        notice_status=NoticeStatus.UNKNOWN,
        notice_start=None,
        notice_end=None,
        hr_checks=HrInputChecks(),
    )
    repository.add(termination)
    loaded = repository.get(termination.termination_id)
    assert loaded.hr_checks.leave is CheckState.UNKNOWN
    assert loaded.hr_checks.leave is not CheckState.NONE
    assert "HR_CHECK_LEAVE_UNKNOWN" in loaded.readiness_errors()
    assert loaded.can_be_ready_for_impact_emploi() is False


def test_non_utc_timestamps_are_stored_in_utc(termination_db):
    paris = timezone(timedelta(hours=2))
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination(
        known_at=datetime(2026, 10, 1, 11, 0, tzinfo=paris),
        created_at=datetime(2026, 10, 1, 12, 0, tzinfo=paris),
    )
    repository.add(termination)
    loaded = repository.get(termination.termination_id)
    assert loaded.known_at == datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    assert loaded.created_at == datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)


def test_one_save_advances_version_by_exactly_one_whatever_the_mutations(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)

    termination.update_transmittable(comments="contrôle 1")
    termination.update_transmittable(comments="contrôle 2")
    termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    assert termination.version == 1
    repository.save(termination)

    assert termination.version == 2
    assert stored_row(termination_db, termination.termination_id)[:2] == (2, "PRET_IMPACT_EMPLOI")
    assert repository.get(termination.termination_id) == termination


def test_saving_twice_the_same_object_is_sequential(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)
    repository.save(termination)
    repository.save(termination)
    assert termination.version == 3
    assert stored_row(termination_db, termination.termination_id)[0] == 3


def test_stale_version_is_a_conflict_and_writes_nothing(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)
    stale = repository.get(termination.termination_id)
    termination.update_transmittable(comments="A")
    repository.save(termination)

    stale.update_transmittable(comments="B")
    with pytest.raises(TerminationVersionConflict) as exc:
        repository.save(stale)
    assert exc.value.code == "TERMINATION_VERSION_CONFLICT"
    assert stale.version == 1
    assert stored_row(termination_db, termination.termination_id)[:4] == (
        2, "A_PREPARER", "contract-1", "A",
    )


def test_add_requires_a_never_persisted_termination(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)
    with pytest.raises(TerminationPersistenceError) as exc:
        repository.add(termination)
    assert exc.value.code == "TERMINATION_ALREADY_PERSISTED"


def test_same_identifier_cannot_be_inserted_twice(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    first = make_termination()
    repository.add(first)
    first.workflow_status = TerminationWorkflowStatus.CLOTURE  # libère l'unicité active
    repository.save(first)
    duplicate = make_termination(termination_id=first.termination_id)
    with pytest.raises(TerminationAlreadyExists):
        repository.add(duplicate)


def test_save_before_add_is_refused(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    with pytest.raises(TerminationPersistenceError) as exc:
        repository.save(make_termination())
    assert exc.value.code == "TERMINATION_NOT_PERSISTED"


def test_save_of_a_missing_row_is_not_found(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    ghost = make_termination(version=1)
    with pytest.raises(TerminationNotFound):
        repository.save(ghost)


def test_contract_of_a_persisted_termination_is_immutable(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)
    termination.contract_id = "contract-2"
    with pytest.raises(TerminationPersistenceError) as exc:
        repository.save(termination)
    assert exc.value.code == "TERMINATION_CONTRACT_IMMUTABLE"
    assert repository.get(termination.termination_id).contract_id == "contract-1"


def test_one_active_termination_per_contract(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    repository.add(make_termination())
    second = make_termination()
    with pytest.raises(ActiveTerminationExists) as exc:
        repository.add(second)
    assert exc.value.code == "ACTIVE_TERMINATION_EXISTS"
    assert second.version == 0
    assert count_rows(termination_db) == 1
    repository.add(make_termination(contract_id="contract-2"))
    assert count_rows(termination_db) == 2


def test_closed_termination_releases_the_active_slot(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)
    for target in (
        TerminationWorkflowStatus.PRET_IMPACT_EMPLOI,
        TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI,
        TerminationWorkflowStatus.EN_ATTENTE_RESULTATS,
        TerminationWorkflowStatus.RESULTATS_RECUS,
        TerminationWorkflowStatus.DOCUMENTS_REMIS,
    ):
        termination.transition_to(target)
    termination.transition_to(TerminationWorkflowStatus.CLOTURE, external_checklist_complete=True)
    repository.save(termination)
    assert stored_row(termination_db, termination.termination_id)[1:3] == ("CLOTURE", None)
    assert repository.get_active_for_contract("contract-1") is None

    later = make_termination()
    repository.add(later)
    assert repository.get_active_for_contract("contract-1") == later
    history = repository.list_for_contract("contract-1")
    assert {item.termination_id for item in history} == {termination.termination_id, later.termination_id}


def test_failed_insert_is_rolled_back(termination_db):
    def fail(point):
        if point == "after_insert":
            raise RuntimeError("panne simulée")

    repository = MySqlContractTerminationRepository(termination_db, failure_injector=fail)
    termination = make_termination()
    with pytest.raises(RuntimeError, match="panne simulée"):
        repository.add(termination)
    assert termination.version == 0
    assert count_rows(termination_db) == 0
    MySqlContractTerminationRepository(termination_db).add(termination)
    assert termination.version == 1


def test_failed_update_is_rolled_back_and_keeps_the_expected_version(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)

    def fail(point):
        if point == "after_update":
            raise RuntimeError("panne simulée")

    termination.update_transmittable(comments="non validé")
    with pytest.raises(RuntimeError, match="panne simulée"):
        MySqlContractTerminationRepository(termination_db, failure_injector=fail).save(termination)
    assert termination.version == 1
    assert stored_row(termination_db, termination.termination_id)[0::3] == (1, "Fin de CDD — heures déjà saisies")
    repository.save(termination)
    assert stored_row(termination_db, termination.termination_id)[0::3] == (2, "non validé")


def test_autocommit_connection_is_refused(termination_db):
    repository = MySqlContractTerminationRepository(lambda: termination_db(autocommit=True))
    with pytest.raises(TerminationPersistenceError) as exc:
        repository.add(make_termination())
    assert exc.value.code == "AUTOCOMMIT_NOT_ALLOWED"
    assert count_rows(termination_db) == 0


def test_schema_is_innodb_and_starts_empty(termination_db):
    conn = termination_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ENGINE FROM information_schema.TABLES"
            " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tw_contract_termination'"
        )
        assert cur.fetchone()[0] == "InnoDB"
        cur.execute(
            "SELECT INDEX_NAME, NON_UNIQUE FROM information_schema.STATISTICS"
            " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tw_contract_termination'"
            " AND COLUMN_NAME = 'active_contract_id'"
        )
        assert cur.fetchall() == [("uq_tw_contract_termination_active", 0)]
    finally:
        conn.close()
    assert count_rows(termination_db) == 0


def test_identifiers_are_case_sensitive(termination_db):
    repository = MySqlContractTerminationRepository(termination_db)
    repository.add(make_termination(contract_id="C-1"))
    repository.add(make_termination(contract_id="c-1"))
    assert repository.get_active_for_contract("C-1").contract_id == "C-1"


def test_no_termination_is_derived_from_contract_end_dates():
    source = (ROOT / "infrastructure" / "persistence" / "mysql_termination_repository.py").read_text(encoding="utf-8")
    schema = (ROOT / "infrastructure" / "persistence" / "sql" / "mysql" / "termination_v1.sql").read_text(encoding="utf-8")
    code_only = "\n".join(line for line in schema.splitlines() if not line.lstrip().startswith("--"))
    for forbidden in ("date_fin", "end_date", "contrats", "contracts"):
        assert forbidden not in source.replace("effective_end_date", "")
        assert forbidden not in code_only.replace("effective_end_date", "")


def test_termination_persistence_does_not_depend_on_dpae():
    for path in (
        ROOT / "domain" / "employment" / "termination.py",
        ROOT / "domain" / "employment" / "termination_repository.py",
        ROOT / "infrastructure" / "persistence" / "mysql_termination_repository.py",
    ):
        assert "dpae" not in path.read_text(encoding="utf-8").lower()
