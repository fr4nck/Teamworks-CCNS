"""SORTIE-002 — concurrence réelle sur MariaDB/MySQL (connexions distinctes).

Chaque scénario utilise deux connexions InnoDB indépendantes. Les scénarios
« bloquants » maintiennent la transaction de A ouverte (verrou de ligne ou de
clé unique réellement tenu) pendant que B tente d'écrire.
"""
from __future__ import annotations

import threading
from datetime import date

import pytest

from domain.employment.termination import TerminationWorkflowStatus
from domain.employment.termination_repository import (
    ActiveTerminationExists,
    TerminationVersionConflict,
)
from infrastructure.persistence.mysql_termination_repository import MySqlContractTerminationRepository
from tests.termination_mysql_support import termination_db, termination_mysql_server  # noqa: F401
from tests.test_termination_mysql_repository import make_termination, stored_row

WAIT = 20.0


class Holder:
    """Injecteur qui garde la transaction de A ouverte jusqu'à ``release``."""

    def __init__(self, point, fail=False):
        self.point = point
        self.fail = fail
        self.reached = threading.Event()
        self.release = threading.Event()

    def __call__(self, name):
        if name != self.point:
            return
        self.reached.set()
        assert self.release.wait(WAIT), "transaction A jamais relâchée"
        if self.fail:
            raise RuntimeError("A annule")


def run_in_thread(fn):
    outcome = {}

    def target():
        try:
            outcome["result"] = fn()
        except BaseException as exc:  # capturé pour assertion dans le test
            outcome["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread, outcome


def test_two_readers_same_version_second_writer_conflicts(termination_db):
    repo = MySqlContractTerminationRepository(termination_db)
    original = make_termination()
    repo.add(original)

    a = repo.get(original.termination_id)
    b = repo.get(original.termination_id)
    assert a.version == b.version == 1

    a.update_transmittable(comments="écrit par A")
    repo.save(a)
    b.update_transmittable(comments="écrit par B")
    with pytest.raises(TerminationVersionConflict):
        repo.save(b)

    assert stored_row(termination_db, original.termination_id)[0::3] == (2, "écrit par A")


def test_blocked_writer_waits_for_the_lock_then_conflicts(termination_db):
    base = MySqlContractTerminationRepository(termination_db)
    original = make_termination()
    base.add(original)
    a = base.get(original.termination_id)
    b = base.get(original.termination_id)
    a.update_transmittable(comments="A")
    b.update_transmittable(comments="B")

    holder = Holder("after_update")
    thread_a, outcome_a = run_in_thread(
        lambda: MySqlContractTerminationRepository(termination_db, failure_injector=holder).save(a)
    )
    assert holder.reached.wait(WAIT)
    thread_b, outcome_b = run_in_thread(lambda: base.save(b))
    thread_b.join(1.0)
    assert thread_b.is_alive(), "B doit attendre le verrou de ligne tenu par A"

    holder.release.set()
    thread_a.join(WAIT)
    thread_b.join(WAIT)
    assert "error" not in outcome_a
    assert isinstance(outcome_b.get("error"), TerminationVersionConflict)
    assert a.version == 2 and b.version == 1
    assert stored_row(termination_db, original.termination_id)[0::3] == (2, "A")


def test_blocked_writer_succeeds_when_first_transaction_rolls_back(termination_db):
    base = MySqlContractTerminationRepository(termination_db)
    original = make_termination()
    base.add(original)
    a = base.get(original.termination_id)
    b = base.get(original.termination_id)
    a.update_transmittable(comments="A")
    b.update_transmittable(comments="B")

    holder = Holder("after_update", fail=True)
    thread_a, outcome_a = run_in_thread(
        lambda: MySqlContractTerminationRepository(termination_db, failure_injector=holder).save(a)
    )
    assert holder.reached.wait(WAIT)
    thread_b, outcome_b = run_in_thread(lambda: base.save(b))
    thread_b.join(1.0)
    assert thread_b.is_alive()

    holder.release.set()
    thread_a.join(WAIT)
    thread_b.join(WAIT)
    assert isinstance(outcome_a.get("error"), RuntimeError)
    assert "error" not in outcome_b
    assert a.version == 1 and b.version == 2
    assert stored_row(termination_db, original.termination_id)[0::3] == (2, "B")


def test_simultaneous_saves_exactly_one_wins(termination_db):
    base = MySqlContractTerminationRepository(termination_db)
    original = make_termination()
    base.add(original)
    copies = [base.get(original.termination_id) for _ in range(4)]
    barrier = threading.Barrier(len(copies))
    results = []

    def writer(index, termination):
        termination.update_transmittable(comments="writer %d" % index)
        barrier.wait(WAIT)
        try:
            MySqlContractTerminationRepository(termination_db).save(termination)
            results.append(("ok", index))
        except TerminationVersionConflict:
            results.append(("conflict", index))

    threads = [threading.Thread(target=writer, args=item) for item in enumerate(copies)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(WAIT)

    winners = [index for status, index in results if status == "ok"]
    assert len(results) == 4 and len(winners) == 1
    row = stored_row(termination_db, original.termination_id)
    assert row[0] == 2
    assert row[3] == "writer %d" % winners[0]


def test_transmission_committed_first_blocks_a_stale_data_change(termination_db):
    base = MySqlContractTerminationRepository(termination_db)
    original = make_termination()
    base.add(original)
    original.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    base.save(original)

    editor = base.get(original.termination_id)
    transmitter = base.get(original.termination_id)
    transmitter.transition_to(TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI)
    base.save(transmitter)

    # Encore PRET dans sa copie : le domaine l'autorise localement…
    editor.update_transmittable(effective_end_date=date(2026, 10, 30), last_worked_date=date(2026, 10, 30))
    # … mais la base refuse d'écraser le dossier transmis.
    with pytest.raises(TerminationVersionConflict):
        base.save(editor)
    loaded = base.get(original.termination_id)
    assert loaded.workflow_status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI
    assert loaded.effective_end_date == date(2026, 10, 31)


def test_closure_committed_first_blocks_a_stale_update(termination_db):
    base = MySqlContractTerminationRepository(termination_db)
    original = make_termination()
    base.add(original)
    stale = base.get(original.termination_id)
    for target in (
        TerminationWorkflowStatus.PRET_IMPACT_EMPLOI,
        TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI,
        TerminationWorkflowStatus.EN_ATTENTE_RESULTATS,
        TerminationWorkflowStatus.RESULTATS_RECUS,
        TerminationWorkflowStatus.DOCUMENTS_REMIS,
    ):
        original.transition_to(target)
    original.transition_to(TerminationWorkflowStatus.CLOTURE, external_checklist_complete=True)
    base.save(original)

    stale.update_transmittable(comments="après clôture")
    with pytest.raises(TerminationVersionConflict):
        base.save(stale)
    row = stored_row(termination_db, original.termination_id)
    assert row[1:3] == ("CLOTURE", None)


def test_concurrent_creations_for_one_contract_keep_a_single_active(termination_db):
    candidates = [make_termination() for _ in range(4)]
    barrier = threading.Barrier(len(candidates))
    results = []

    def creator(termination):
        barrier.wait(WAIT)
        try:
            MySqlContractTerminationRepository(termination_db).add(termination)
            results.append("ok")
        except ActiveTerminationExists:
            results.append("active-exists")

    threads = [threading.Thread(target=creator, args=(item,)) for item in candidates]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(WAIT)

    assert sorted(results) == ["active-exists"] * 3 + ["ok"]
    conn = termination_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tw_contract_termination WHERE contract_id = 'contract-1'")
        assert cur.fetchone()[0] == 1
    finally:
        conn.close()


@pytest.mark.parametrize("first_rolls_back", [False, True])
def test_second_creation_waits_on_the_unique_key(termination_db, first_rolls_back):
    first, second = make_termination(), make_termination()
    holder = Holder("after_insert", fail=first_rolls_back)
    thread_a, outcome_a = run_in_thread(
        lambda: MySqlContractTerminationRepository(termination_db, failure_injector=holder).add(first)
    )
    assert holder.reached.wait(WAIT)
    thread_b, outcome_b = run_in_thread(lambda: MySqlContractTerminationRepository(termination_db).add(second))
    thread_b.join(1.0)
    assert thread_b.is_alive(), "B doit attendre la clé unique réservée par A"

    holder.release.set()
    thread_a.join(WAIT)
    thread_b.join(WAIT)
    active = MySqlContractTerminationRepository(termination_db).get_active_for_contract("contract-1")
    if first_rolls_back:
        assert isinstance(outcome_a.get("error"), RuntimeError)
        assert "error" not in outcome_b
        assert active.termination_id == second.termination_id
    else:
        assert "error" not in outcome_a
        assert isinstance(outcome_b.get("error"), ActiveTerminationExists)
        assert active.termination_id == first.termination_id
