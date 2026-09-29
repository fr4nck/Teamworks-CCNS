"""SORTIE-003 — transmission, snapshots et corrections sur un vrai MySQL/MariaDB."""
from __future__ import annotations

import hashlib
import unicodedata
from datetime import date, datetime, timedelta, timezone

import pytest

from domain.employment.termination import (
    CorrectionRequest,
    TerminationDomainError,
    TerminationWorkflowStatus,
)
from domain.employment.termination_repository import (
    CommandIdempotencyConflict,
    SnapshotIntegrityError,
    TerminationNotFound,
    TerminationPersistenceError,
    TerminationVersionConflict,
    TransmissionRetryExhausted,
)
from domain.employment.termination_transmission import (
    CommunicatedHrItem,
    RequestCorrection,
    TransmissionChannel,
    canonical_transmission_payload,
    sha256_hex,
)
from infrastructure.persistence.mysql_termination_repository import MySqlContractTerminationRepository
from infrastructure.persistence.mysql_termination_transmission_store import MySqlTerminationTransmissionStore
from tests.termination_mysql_support import termination_db, termination_mysql_server  # noqa: F401
from tests.termination_transmission_support import RECORDED_AT, TRANSMITTED_AT, fixed_clock, transmit_command
from tests.test_termination_mysql_repository import make_termination

LATER = RECORDED_AT + timedelta(hours=2)


def later_clock():
    return LATER + timedelta(hours=1)


def ready(connect, **overrides):
    repository = MySqlContractTerminationRepository(connect)
    termination = make_termination(**overrides)
    repository.add(termination)
    termination.transition_to(TerminationWorkflowStatus.PRET_IMPACT_EMPLOI)
    repository.save(termination)
    return termination


def store(connect, **kwargs):
    kwargs.setdefault("clock", fixed_clock)
    return MySqlTerminationTransmissionStore(connect, **kwargs)


def scalar(connect, sql, params=()):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()[0]
    finally:
        conn.close()


def rows(connect, table):
    return scalar(connect, "SELECT COUNT(*) FROM " + table)


def raw(connect, sql, params=()):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def open_correction(connect, termination_id, *, reason="Date de fin erronée", command_id="corr-1"):
    repository = MySqlContractTerminationRepository(connect)
    current = repository.get(termination_id)
    store(connect, clock=lambda: LATER).request_correction(
        RequestCorrection(command_id, termination_id, current.version, reason, "director-1")
    )
    current = repository.get(termination_id)
    current.update_transmittable(effective_end_date=date(2026, 10, 30), last_worked_date=date(2026, 10, 30))
    repository.save(current)
    return current


def correction_command(termination, **overrides):
    values = dict(transmitted_at=LATER + timedelta(minutes=30), channel=TransmissionChannel.PORTAL)
    values.update(overrides)
    return transmit_command(termination, **values)


# ----------------------------------------------------------------- schéma

def test_schema_tables_constraints_and_payload_type(termination_db):
    conn = termination_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()"
            " AND TABLE_NAME IN ('tw_termination_transmission_snapshot', 'tw_termination_command')"
        )
        assert dict(cur.fetchall()) == {
            "tw_termination_transmission_snapshot": "InnoDB", "tw_termination_command": "InnoDB",
        }
        cur.execute(
            "SELECT DATA_TYPE, COLLATION_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE()"
            " AND TABLE_NAME = 'tw_termination_transmission_snapshot' AND COLUMN_NAME = 'canonical_payload'"
        )
        assert cur.fetchone() == ("longtext", "utf8mb4_bin")
        cur.execute(
            "SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX), MAX(NON_UNIQUE)"
            " FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE()"
            " AND TABLE_NAME = 'tw_termination_transmission_snapshot' GROUP BY INDEX_NAME"
        )
        indexes = {name: (columns, int(non_unique)) for name, columns, non_unique in cur.fetchall()}
        assert indexes["PRIMARY"] == ("snapshot_id", 0)
        assert indexes["uq_tw_termination_snapshot_version"] == ("termination_id,version", 0)
        assert indexes["uq_tw_termination_snapshot_supersedes"] == ("supersedes_snapshot_id", 0)
        cur.execute(
            "SELECT CONSTRAINT_NAME, REFERENCED_TABLE_NAME FROM information_schema.REFERENTIAL_CONSTRAINTS"
            " WHERE CONSTRAINT_SCHEMA = DATABASE()"
        )
        assert set(cur.fetchall()) >= {
            ("fk_tw_termination_snapshot_termination", "tw_contract_termination"),
            ("fk_tw_termination_snapshot_supersedes", "tw_termination_transmission_snapshot"),
            ("fk_tw_termination_command_termination", "tw_contract_termination"),
            ("fk_tw_termination_command_snapshot", "tw_termination_transmission_snapshot"),
        }
    finally:
        conn.close()


# ----------------------------------------------------------------- V1

def test_first_transmission_is_atomic_and_complete(termination_db):
    termination = ready(termination_db)
    result = store(termination_db).transmit(transmit_command(termination, external_reference="mail 3/11"))
    snapshot = result.snapshot
    assert (result.replayed, result.termination_version, snapshot.version) == (False, 3, 1)
    assert snapshot.created_at == RECORDED_AT and snapshot.transmitted_at == TRANSMITTED_AT
    assert snapshot.external_reference == "mail 3/11"

    loaded = MySqlContractTerminationRepository(termination_db).get(termination.termination_id)
    assert loaded.workflow_status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI
    assert loaded.version == 3
    [stored] = store(termination_db).list_snapshots(termination.termination_id)
    assert stored == snapshot
    expected = canonical_transmission_payload(termination, transmit_command(termination).hr_items)
    assert stored.canonical_payload == expected
    assert stored.payload_hash == hashlib.sha256(expected.encode("utf-8")).hexdigest()


def test_payload_roundtrips_byte_for_byte_with_unicode(termination_db):
    termination = ready(termination_db)
    description = unicodedata.normalize("NFD", "Congés « payés » — Hélène 😀 ☃")
    items = (CommunicatedHrItem("absences", "Arrêt"), CommunicatedHrItem("leave", description))
    result = store(termination_db).transmit(transmit_command(termination, hr_items=items))
    stored_bytes = scalar(
        termination_db,
        "SELECT canonical_payload FROM tw_termination_transmission_snapshot WHERE snapshot_id = %s",
        (result.snapshot.snapshot_id,),
    ).encode("utf-8")
    assert stored_bytes == result.snapshot.canonical_payload.encode("utf-8")
    assert hashlib.sha256(stored_bytes).hexdigest() == result.snapshot.payload_hash
    assert unicodedata.normalize("NFC", description) in stored_bytes.decode("utf-8")
    assert scalar(
        termination_db,
        "SELECT payload_hash FROM tw_termination_transmission_snapshot WHERE snapshot_id = %s",
        (result.snapshot.snapshot_id,),
    ) == result.snapshot.payload_hash


def test_audit_trail_has_ids_versions_hash_actor_but_no_payload(termination_db):
    termination = ready(termination_db)
    result = store(termination_db).transmit(transmit_command(termination, command_id="cmd-v1"))
    [entry] = store(termination_db).audit_trail(termination.termination_id)
    assert entry["command_id"] == "cmd-v1" and entry["command_type"] == "TRANSMIT"
    assert entry["snapshot_id"] == result.snapshot.snapshot_id and entry["snapshot_version"] == 1
    assert entry["payload_hash"] == result.snapshot.payload_hash
    assert (entry["termination_version_before"], entry["termination_version_after"]) == (2, 3)
    assert entry["actor_id"] == "director-1" and entry["recorded_at"] == RECORDED_AT
    conn = termination_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tw_termination_command")
        flat = " ".join(str(value) for value in cur.fetchone())
    finally:
        conn.close()
    assert "détail communiqué" not in flat and "2026-10-31" not in flat


def test_replay_after_commit_returns_the_same_v1(termination_db):
    termination = ready(termination_db)
    command = transmit_command(termination, command_id="cmd-lost-response")
    first = store(termination_db).transmit(command)
    second = store(termination_db, clock=later_clock).transmit(command)  # réponse perdue, même commande
    assert second.replayed is True and second.snapshot == first.snapshot
    assert second.termination_version == first.termination_version == 3
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 1
    assert rows(termination_db, "tw_termination_command") == 1


def test_same_command_id_with_other_content_is_an_explicit_conflict(termination_db):
    termination = ready(termination_db)
    store(termination_db).transmit(transmit_command(termination, command_id="cmd-1"))
    with pytest.raises(CommandIdempotencyConflict) as exc:
        store(termination_db).transmit(transmit_command(termination, command_id="cmd-1", channel="PORTAL"))
    assert exc.value.code == "COMMAND_IDEMPOTENCY_CONFLICT"
    with pytest.raises(CommandIdempotencyConflict):
        store(termination_db).request_correction(
            RequestCorrection("cmd-1", termination.termination_id, 3, "erreur", "director-1")
        )
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 1


def test_a_new_command_cannot_create_a_second_v1(termination_db):
    termination = ready(termination_db)
    store(termination_db).transmit(transmit_command(termination))
    with pytest.raises(TerminationDomainError) as exc:
        store(termination_db).transmit(transmit_command(termination, expected_version=3))
    assert exc.value.code == "SNAPSHOT_ALREADY_TRANSMITTED"
    with pytest.raises(TerminationVersionConflict):
        store(termination_db).transmit(transmit_command(termination))  # version 2 obsolète
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 1


@pytest.mark.parametrize("draft", [True, False])
def test_refused_transmissions_write_nothing(termination_db, draft):
    repository = MySqlContractTerminationRepository(termination_db)
    termination = make_termination()
    repository.add(termination)
    if draft:
        with pytest.raises(TerminationDomainError) as exc:
            store(termination_db).transmit(transmit_command(termination))
        assert exc.value.code == "NOT_READY_FOR_TRANSMISSION"
    else:
        with pytest.raises(TerminationNotFound):
            store(termination_db).transmit(transmit_command(make_termination(contract_id="ghost")))
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 0
    assert rows(termination_db, "tw_termination_command") == 0
    assert repository.get(termination.termination_id).version == 1


def test_plain_save_can_never_cross_into_transmitted(termination_db):
    termination = ready(termination_db)
    termination.workflow_status = TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI  # contournement du domaine
    with pytest.raises(TerminationPersistenceError) as exc:
        MySqlContractTerminationRepository(termination_db).save(termination)
    assert exc.value.code == "TRANSMISSION_REQUIRES_SNAPSHOT"
    loaded = MySqlContractTerminationRepository(termination_db).get(termination.termination_id)
    assert loaded.workflow_status is TerminationWorkflowStatus.PRET_IMPACT_EMPLOI


def test_plain_save_can_never_open_or_close_a_correction(termination_db):
    termination = ready(termination_db)
    store(termination_db).transmit(transmit_command(termination))
    repository = MySqlContractTerminationRepository(termination_db)
    loaded = repository.get(termination.termination_id)
    loaded.open_correction = CorrectionRequest("contournement", LATER, "director-1")
    with pytest.raises(TerminationPersistenceError) as exc:
        repository.save(loaded)
    assert exc.value.code == "CORRECTION_STATE_REQUIRES_COMMAND"
    open_correction(termination_db, termination.termination_id)
    loaded = repository.get(termination.termination_id)
    loaded.open_correction = None
    with pytest.raises(TerminationPersistenceError):
        repository.save(loaded)
    assert repository.get(termination.termination_id).has_open_correction


# ----------------------------------------------------------------- correction V2

def test_correction_creates_v2_and_leaves_v1_intact(termination_db):
    termination = ready(termination_db)
    v1 = store(termination_db).transmit(transmit_command(termination)).snapshot
    conn = termination_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tw_termination_transmission_snapshot WHERE snapshot_id = %s", (v1.snapshot_id,))
        v1_row = cur.fetchone()
    finally:
        conn.close()

    corrected = open_correction(termination_db, termination.termination_id)
    assert corrected.has_open_correction and corrected.open_correction.requested_at == LATER
    result = store(termination_db, clock=later_clock).transmit_correction(
        correction_command(corrected, command_id="cmd-v2")
    )
    v2 = result.snapshot
    assert (v2.version, v2.supersedes_snapshot_id, v2.correction_reason) == (2, v1.snapshot_id, "Date de fin erronée")
    assert v2.payload["effective_end_date"] == "2026-10-30" and v2.channel is TransmissionChannel.PORTAL

    history = store(termination_db).list_snapshots(termination.termination_id)
    assert [s.version for s in history] == [1, 2]
    assert history[0] == v1 and history[0].payload["effective_end_date"] == "2026-10-31"
    conn = termination_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tw_termination_transmission_snapshot WHERE snapshot_id = %s", (v1.snapshot_id,))
        assert cur.fetchone() == v1_row
    finally:
        conn.close()

    loaded = MySqlContractTerminationRepository(termination_db).get(termination.termination_id)
    assert loaded.open_correction is None
    assert loaded.workflow_status is TerminationWorkflowStatus.TRANSMIS_IMPACT_EMPLOI
    trail = store(termination_db).audit_trail(termination.termination_id)
    assert [(e["command_type"], e["snapshot_version"]) for e in trail] == [
        ("TRANSMIT", 1), ("REQUEST_CORRECTION", None), ("TRANSMIT_CORRECTION", 2),
    ]
    assert [(e["termination_version_before"], e["termination_version_after"]) for e in trail] == [
        (2, 3), (3, 4), (5, 6),
    ]


def test_correction_request_is_idempotent(termination_db):
    termination = ready(termination_db)
    store(termination_db).transmit(transmit_command(termination))
    command = RequestCorrection("corr-1", termination.termination_id, 3, "erreur de date", "director-1")
    first = store(termination_db, clock=lambda: LATER).request_correction(command)
    second = store(termination_db, clock=later_clock).request_correction(command)
    assert (first.replayed, second.replayed) == (False, True)
    assert first.termination_version == second.termination_version == 4
    assert rows(termination_db, "tw_termination_command") == 2


def test_correction_transmission_rules(termination_db):
    termination = ready(termination_db)
    store(termination_db).transmit(transmit_command(termination))
    current = MySqlContractTerminationRepository(termination_db).get(termination.termination_id)
    with pytest.raises(TerminationDomainError) as exc:
        store(termination_db, clock=later_clock).transmit_correction(correction_command(current))
    assert exc.value.code == "CORRECTION_NOT_OPEN"
    store(termination_db, clock=lambda: LATER).request_correction(
        RequestCorrection("corr-1", termination.termination_id, 3, "vérification", "director-1")
    )
    current = MySqlContractTerminationRepository(termination_db).get(termination.termination_id)
    with pytest.raises(TerminationDomainError) as exc:
        store(termination_db, clock=later_clock).transmit_correction(correction_command(current))
    assert exc.value.code == "CORRECTION_WITHOUT_CHANGE"
    with pytest.raises(TerminationNotFound):
        store(termination_db).transmit_correction(transmit_command(make_termination(contract_id="c-2")))
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 1


def test_closed_termination_cannot_be_corrected(termination_db):
    termination = ready(termination_db)
    store(termination_db).transmit(transmit_command(termination))
    repository = MySqlContractTerminationRepository(termination_db)
    current = repository.get(termination.termination_id)
    for target in (TerminationWorkflowStatus.EN_ATTENTE_RESULTATS, TerminationWorkflowStatus.RESULTATS_RECUS,
                   TerminationWorkflowStatus.DOCUMENTS_REMIS):
        current.transition_to(target)
    current.transition_to(TerminationWorkflowStatus.CLOTURE, external_checklist_complete=True)
    repository.save(current)
    with pytest.raises(TerminationDomainError) as exc:
        store(termination_db).request_correction(
            RequestCorrection("corr-x", termination.termination_id, current.version, "trop tard", "d")
        )
    assert exc.value.code == "TERMINATION_CLOSED"


# ----------------------------------------------------------------- contraintes base

def test_snapshots_and_commands_are_append_only_in_the_database(termination_db):
    termination = ready(termination_db)
    snapshot = store(termination_db).transmit(transmit_command(termination, command_id="cmd-1")).snapshot
    for sql in (
        "UPDATE tw_termination_transmission_snapshot SET canonical_payload = '{}' WHERE snapshot_id = %s",
        "UPDATE tw_termination_transmission_snapshot SET payload_hash = REPEAT('0', 64) WHERE snapshot_id = %s",
        "DELETE FROM tw_termination_transmission_snapshot WHERE snapshot_id = %s",
    ):
        with pytest.raises(Exception) as exc:
            raw(termination_db, sql, (snapshot.snapshot_id,))
        assert "append-only" in str(exc.value)
    for sql in ("UPDATE tw_termination_command SET actor_id = 'x'", "DELETE FROM tw_termination_command"):
        with pytest.raises(Exception) as exc:
            raw(termination_db, sql)
        assert "append-only" in str(exc.value)
    assert store(termination_db).get_snapshot(snapshot.snapshot_id) == snapshot


def _raw_snapshot(snapshot_id, termination_id, version, supersedes=None, reason=None):
    return (
        "INSERT INTO tw_termination_transmission_snapshot (snapshot_id, termination_id, version,"
        " canonical_payload, payload_hash, created_at, created_by, transmitted_at, transmitted_by, channel,"
        " supersedes_snapshot_id, correction_reason) VALUES (%s, %s, %s, '{}', REPEAT('a', 64),"
        " '2026-11-03 10:00:00', 'x', '2026-11-03 09:00:00', 'x', 'EMAIL', %s, %s)",
        (snapshot_id, termination_id, version, supersedes, reason),
    )


def _errno_of(connect, statement):
    with pytest.raises(Exception) as exc:
        raw(connect, *statement)
    return getattr(exc.value, "errno", None)


def test_database_enforces_version_uniqueness_fk_and_idempotency(termination_db):
    first = ready(termination_db)
    other = ready(termination_db, contract_id="contract-2")
    v1 = store(termination_db).transmit(transmit_command(first, command_id="cmd-1")).snapshot
    other_v1 = store(termination_db).transmit(transmit_command(other, command_id="cmd-2")).snapshot

    assert _errno_of(termination_db, _raw_snapshot("dup", first.termination_id, 1)) == 1062
    assert _errno_of(termination_db, _raw_snapshot("orphan", "no-such-termination", 1)) == 1452
    assert _errno_of(termination_db, _raw_snapshot(
        "foreign", first.termination_id, 2, other_v1.snapshot_id, "r")) == 1452
    raw(termination_db, *_raw_snapshot("v2", first.termination_id, 2, v1.snapshot_id, "r"))
    assert _errno_of(termination_db, _raw_snapshot("fork", first.termination_id, 3, v1.snapshot_id, "r")) == 1062
    assert _errno_of(termination_db, (
        "INSERT INTO tw_termination_command (command_id, command_type, command_hash, termination_id,"
        " termination_version_before, termination_version_after, actor_id, recorded_at)"
        " VALUES ('cmd-1', 'TRANSMIT', REPEAT('b', 64), %s, 3, 4, 'x', '2026-11-03 10:00:00')",
        (other.termination_id,),
    )) == 1062


def test_tampering_behind_the_triggers_is_detected_on_read(termination_db):
    termination = ready(termination_db)
    snapshot = store(termination_db).transmit(transmit_command(termination)).snapshot
    raw(termination_db, "DROP TRIGGER trg_tw_termination_snapshot_no_update")
    raw(
        termination_db,
        "UPDATE tw_termination_transmission_snapshot SET canonical_payload = REPLACE(canonical_payload,"
        " '2026-10-31', '2026-10-30') WHERE snapshot_id = %s",
        (snapshot.snapshot_id,),
    )
    with pytest.raises(SnapshotIntegrityError) as exc:
        store(termination_db).list_snapshots(termination.termination_id)
    assert exc.value.code == "SNAPSHOT_HASH_MISMATCH"


# ----------------------------------------------------------------- rollback

@pytest.mark.parametrize("point", [
    "after_snapshot_insert", "after_command_insert", "after_termination_update", "before_commit",
])
def test_any_failure_before_commit_rolls_everything_back(termination_db, point):
    termination = ready(termination_db)

    def fail(name):
        if name == point:
            raise RuntimeError("panne " + name)

    command = transmit_command(termination, command_id="cmd-1")
    with pytest.raises(RuntimeError):
        store(termination_db, failure_injector=fail).transmit(command)
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 0
    assert rows(termination_db, "tw_termination_command") == 0
    loaded = MySqlContractTerminationRepository(termination_db).get(termination.termination_id)
    assert (loaded.workflow_status, loaded.version) == (TerminationWorkflowStatus.PRET_IMPACT_EMPLOI, 2)
    result = store(termination_db).transmit(command)  # la même commande aboutit ensuite
    assert result.replayed is False and result.snapshot.version == 1


class ReusedConnection:
    """Connexion réutilisée (type pool) : close() ne ferme pas réellement."""

    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def close(self):
        pass


def test_rollback_is_explicit_even_with_a_reused_connection(termination_db):
    shared = ReusedConnection(termination_db())
    first = ready(termination_db)
    second = ready(termination_db, contract_id="contract-2")

    def fail(name):
        if name == "after_command_insert":
            raise RuntimeError("panne")

    with pytest.raises(RuntimeError):
        store(lambda: shared, failure_injector=fail).transmit(transmit_command(first, command_id="cmd-1"))
    # Un autre composant qui partage la connexion valide sa propre transaction :
    # sans rollback explicite, le snapshot orphelin partirait avec lui.
    shared._connection.commit()
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 0
    assert rows(termination_db, "tw_termination_command") == 0
    store(lambda: shared).transmit(transmit_command(second, command_id="cmd-2"))
    shared._connection.close()
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 1
    assert store(termination_db).list_snapshots(first.termination_id) == []


# ----------------------------------------------------------------- retry 1213 ciblé

class FakeDeadlock(Exception):
    errno = 1213


def test_deadlock_retries_the_whole_transaction_once_and_records_one_v1(termination_db):
    termination = ready(termination_db)
    calls = []

    def once(name):
        if name == "after_command_insert":
            calls.append(name)
            if len(calls) == 1:
                raise FakeDeadlock("Deadlock found when trying to get lock")

    sleeps = []
    s = store(termination_db, failure_injector=once, sleep=sleeps.append)
    result = s.transmit(transmit_command(termination, command_id="cmd-1"))
    assert s.last_attempts == 2 and len(sleeps) == 1 and result.replayed is False
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 1
    assert rows(termination_db, "tw_termination_command") == 1


def test_deadlock_retry_is_bounded_and_leaves_nothing(termination_db):
    termination = ready(termination_db)

    def always(name):
        if name == "after_snapshot_insert":
            raise FakeDeadlock("deadlock")

    s = store(termination_db, failure_injector=always, sleep=lambda _: None, max_attempts=3)
    with pytest.raises(TransmissionRetryExhausted) as exc:
        s.transmit(transmit_command(termination))
    assert exc.value.code == "TRANSMISSION_DEADLOCK_RETRY_EXHAUSTED" and s.last_attempts == 3
    assert rows(termination_db, "tw_termination_transmission_snapshot") == 0


def test_other_errors_are_never_retried(termination_db):
    termination = ready(termination_db)

    class LockTimeout(Exception):
        errno = 1205

    def fail(name):
        if name == "after_snapshot_insert":
            raise LockTimeout("lock wait timeout")

    s = store(termination_db, failure_injector=fail, sleep=lambda _: pytest.fail("no retry expected"))
    with pytest.raises(LockTimeout):
        s.transmit(transmit_command(termination))
    assert s.last_attempts == 1
