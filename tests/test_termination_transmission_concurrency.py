"""SORTIE-003 — concurrence réelle (connexions InnoDB distinctes) sur les transmissions."""
from __future__ import annotations

import threading
import time
from datetime import timedelta

import pytest

from domain.employment.termination import TerminationDomainError, TerminationWorkflowStatus
from domain.employment.termination_repository import CommandIdempotencyConflict, TerminationVersionConflict
from domain.employment.termination_transmission import RequestCorrection
from infrastructure.persistence.mysql_termination_repository import MySqlContractTerminationRepository
from tests.termination_mysql_support import termination_db, termination_mysql_server  # noqa: F401
from tests.termination_transmission_support import transmit_command
from tests.test_termination_mysql_concurrency import Holder, run_in_thread
from tests.test_termination_transmission_mysql import (
    LATER,
    correction_command,
    later_clock,
    open_correction,
    ready,
    rows,
    store,
)

WAIT = 20.0


def run_together(callables):
    barrier = threading.Barrier(len(callables))
    outcomes = [None] * len(callables)

    def worker(index, fn):
        barrier.wait(WAIT)
        try:
            outcomes[index] = ("ok", fn())
        except BaseException as exc:  # capturé pour assertion
            outcomes[index] = ("error", exc)

    threads = [threading.Thread(target=worker, args=item, daemon=True) for item in enumerate(callables)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(WAIT)
    assert all(outcome is not None for outcome in outcomes), "worker bloqué"
    return outcomes


def snapshot_versions(connect, termination_id):
    return [s.version for s in store(connect).list_snapshots(termination_id)]


# A — double V1
def test_a_concurrent_first_transmissions_create_a_single_v1(termination_db):
    termination = ready(termination_db)
    outcomes = run_together([
        (lambda i=i: store(termination_db).transmit(transmit_command(termination, command_id="w%d" % i)))
        for i in range(4)
    ])
    winners = [value for status, value in outcomes if status == "ok"]
    losers = [value for status, value in outcomes if status == "error"]
    assert len(winners) == 1 and len(losers) == 3
    assert all(isinstance(error, TerminationVersionConflict) for error in losers)
    assert snapshot_versions(termination_db, termination.termination_id) == [1]
    assert rows(termination_db, "tw_termination_command") == 1


def test_a_second_worker_waits_on_the_lock_then_conflicts(termination_db):
    termination = ready(termination_db)
    holder = Holder("after_command_insert")
    thread_a, outcome_a = run_in_thread(
        lambda: store(termination_db, failure_injector=holder).transmit(transmit_command(termination, command_id="a"))
    )
    assert holder.reached.wait(WAIT)
    thread_b, outcome_b = run_in_thread(
        lambda: store(termination_db).transmit(transmit_command(termination, command_id="b"))
    )
    thread_b.join(1.0)
    assert thread_b.is_alive(), "B doit attendre le verrou de la sortie tenu par A"
    holder.release.set()
    thread_a.join(WAIT)
    thread_b.join(WAIT)
    assert "error" not in outcome_a
    assert isinstance(outcome_b.get("error"), TerminationVersionConflict)
    assert snapshot_versions(termination_db, termination.termination_id) == [1]


# B — rejeu concurrent de la même commande (double clic)
def test_b_same_command_submitted_concurrently_is_applied_once(termination_db):
    termination = ready(termination_db)
    command = transmit_command(termination, command_id="double-click")
    outcomes = run_together([lambda: store(termination_db).transmit(command) for _ in range(4)])
    assert all(status == "ok" for status, _ in outcomes)
    results = [value for _, value in outcomes]
    assert sorted(result.replayed for result in results) == [False, True, True, True]
    assert len({result.snapshot.snapshot_id for result in results}) == 1
    assert snapshot_versions(termination_db, termination.termination_id) == [1]
    assert rows(termination_db, "tw_termination_command") == 1


def test_b_replay_waits_for_the_first_commit_then_replays(termination_db):
    termination = ready(termination_db)
    command = transmit_command(termination, command_id="retry-after-timeout")
    holder = Holder("before_commit")
    thread_a, outcome_a = run_in_thread(lambda: store(termination_db, failure_injector=holder).transmit(command))
    assert holder.reached.wait(WAIT)
    thread_b, outcome_b = run_in_thread(lambda: store(termination_db).transmit(command))
    thread_b.join(1.0)
    assert thread_b.is_alive()
    holder.release.set()
    thread_a.join(WAIT)
    thread_b.join(WAIT)
    assert outcome_a["result"].replayed is False
    assert outcome_b["result"].replayed is True
    assert outcome_b["result"].snapshot == outcome_a["result"].snapshot


# C — même command_id, contenu ou sortie différents
def test_c_same_command_id_with_different_content_concurrently(termination_db):
    termination = ready(termination_db)
    outcomes = run_together([
        lambda: store(termination_db).transmit(transmit_command(termination, command_id="shared", channel="EMAIL")),
        lambda: store(termination_db).transmit(transmit_command(termination, command_id="shared", channel="PORTAL")),
    ])
    errors = [value for status, value in outcomes if status == "error"]
    assert len(errors) == 1 and isinstance(errors[0], CommandIdempotencyConflict)
    assert snapshot_versions(termination_db, termination.termination_id) == [1]


def test_c_same_command_id_on_two_terminations_concurrently(termination_db):
    first = ready(termination_db)
    second = ready(termination_db, contract_id="contract-2")
    holder = Holder("after_command_insert")
    thread_a, outcome_a = run_in_thread(
        lambda: store(termination_db, failure_injector=holder).transmit(transmit_command(first, command_id="same"))
    )
    assert holder.reached.wait(WAIT)
    thread_b, outcome_b = run_in_thread(
        lambda: store(termination_db).transmit(transmit_command(second, command_id="same"))
    )
    thread_b.join(1.0)
    assert thread_b.is_alive(), "B attend la clé primaire du command_id réservée par A"
    holder.release.set()
    thread_a.join(WAIT)
    thread_b.join(WAIT)
    assert "error" not in outcome_a
    assert isinstance(outcome_b.get("error"), CommandIdempotencyConflict)
    assert snapshot_versions(termination_db, second.termination_id) == []
    assert MySqlContractTerminationRepository(termination_db).get(second.termination_id).workflow_status is (
        TerminationWorkflowStatus.PRET_IMPACT_EMPLOI
    )


# D — double V2
def _transmitted_with_open_correction(connect):
    termination = ready(connect)
    store(connect).transmit(transmit_command(termination))
    return open_correction(connect, termination.termination_id)


def test_d_concurrent_corrections_create_a_single_v2(termination_db):
    corrected = _transmitted_with_open_correction(termination_db)
    outcomes = run_together([
        (lambda i=i: store(termination_db, clock=later_clock).transmit_correction(
            correction_command(corrected, command_id="v2-%d" % i)))
        for i in range(4)
    ])
    assert sum(status == "ok" for status, _ in outcomes) == 1
    assert all(isinstance(value, TerminationVersionConflict) for status, value in outcomes if status == "error")
    assert snapshot_versions(termination_db, corrected.termination_id) == [1, 2]


def test_d_same_correction_command_replayed_concurrently(termination_db):
    corrected = _transmitted_with_open_correction(termination_db)
    command = correction_command(corrected, command_id="v2-same")
    outcomes = run_together([
        lambda: store(termination_db, clock=later_clock).transmit_correction(command) for _ in range(3)
    ])
    assert sorted(value.replayed for _, value in outcomes) == [False, True, True]
    assert snapshot_versions(termination_db, corrected.termination_id) == [1, 2]


# E — transmission contre correction, correction contre clôture
def test_e_transmission_racing_a_correction_request_never_yields_an_impossible_state(termination_db):
    for _ in range(5):
        termination = ready(termination_db, contract_id="race-%s" % time.monotonic_ns())
        outcomes = run_together([
            lambda: store(termination_db).transmit(transmit_command(termination)),
            lambda: store(termination_db, clock=lambda: LATER).request_correction(
                RequestCorrection("corr-" + termination.termination_id, termination.termination_id, 2, "x", "d")),
        ])
        assert outcomes[0][0] == "ok"
        assert outcomes[1][0] == "error"
        assert isinstance(outcomes[1][1], (TerminationVersionConflict, TerminationDomainError))
        loaded = MySqlContractTerminationRepository(termination_db).get(termination.termination_id)
        assert loaded.workflow_status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI
        assert loaded.open_correction is None
        assert snapshot_versions(termination_db, termination.termination_id) == [1]


def test_e_closure_from_a_stale_copy_cannot_hide_an_open_correction(termination_db):
    termination = ready(termination_db)
    store(termination_db).transmit(transmit_command(termination))
    repository = MySqlContractTerminationRepository(termination_db)
    closer = repository.get(termination.termination_id)
    for target in (TerminationWorkflowStatus.EN_ATTENTE_RESULTATS, TerminationWorkflowStatus.RESULTATS_RECUS,
                   TerminationWorkflowStatus.DOCUMENTS_REMIS):
        closer.transition_to(target)
    repository.save(closer)
    stale = repository.get(termination.termination_id)
    store(termination_db, clock=lambda: LATER).request_correction(
        RequestCorrection("corr", termination.termination_id, closer.version, "erreur", "director-1"))
    stale.transition_to(TerminationWorkflowStatus.CLOTURE, external_checklist_complete=True)
    with pytest.raises(TerminationVersionConflict):
        repository.save(stale)
    fresh = repository.get(termination.termination_id)
    with pytest.raises(TerminationDomainError) as exc:
        fresh.transition_to(TerminationWorkflowStatus.CLOTURE, external_checklist_complete=True)
    assert exc.value.code == "CORRECTION_OPEN"
    assert fresh.workflow_status is TerminationWorkflowStatus.DOCUMENTS_REMIS


# H — vrai interblocage InnoDB 1213, transaction rejouée
def test_h_real_innodb_deadlock_is_retried_and_records_exactly_one_v2(termination_db):
    corrected = _transmitted_with_open_correction(termination_db)
    v1 = store(termination_db).list_snapshots(corrected.termination_id)[0]

    blocker = termination_db()
    cur = blocker.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS tw_test_ballast (id INT PRIMARY KEY) ENGINE=InnoDB")
    blocker.commit()
    cur.execute("DELETE FROM tw_test_ballast")
    cur.executemany("INSERT INTO tw_test_ballast (id) VALUES (%s)", [(i,) for i in range(500)])
    # Verrou exclusif sur l'entrée d'index que la clé étrangère de supersession de
    # V2 doit verrouiller en partagé : l'insertion de V2 l'attendra.
    cur.execute("SELECT snapshot_id FROM tw_termination_transmission_snapshot"
                " FORCE INDEX (uq_tw_termination_snapshot_owner)"
                " WHERE termination_id = %s AND snapshot_id = %s FOR UPDATE",
                (corrected.termination_id, v1.snapshot_id))
    cur.fetchall()

    reached = threading.Event()
    attempts = []

    def injector(name):
        if name == "attempt":
            attempts.append(name)
        if name == "before_snapshot_insert" and len(attempts) == 1:
            reached.set()

    worker = store(termination_db, clock=later_clock, failure_injector=injector, retry_backoff_seconds=0.01)
    thread, outcome = run_in_thread(
        lambda: worker.transmit_correction(correction_command(corrected, command_id="v2-deadlock"))
    )
    assert reached.wait(WAIT)
    time.sleep(0.5)  # le worker tient la sortie et attend V1
    # Le bloqueur réclame la sortie tenue par le worker : cycle -> 1213 pour le plus léger (le worker).
    cur.execute("SELECT termination_id FROM tw_contract_termination WHERE termination_id = %s FOR UPDATE",
                (corrected.termination_id,))
    cur.fetchall()
    blocker.commit()
    cur.execute("DROP TABLE tw_test_ballast")
    blocker.close()
    thread.join(WAIT)

    assert "error" not in outcome, outcome.get("error")
    assert worker.last_attempts == 2, "une seule relance après l'interblocage"
    assert outcome["result"].snapshot.version == 2 and outcome["result"].replayed is False
    assert snapshot_versions(termination_db, corrected.termination_id) == [1, 2]
    assert rows(termination_db, "tw_termination_command") == 3
