"""Contrat d'intégration de MysqlDpaeRepository sur une vraie base."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest

mysql = pytest.importorskip("mysql.connector")

from domain.dpae.model import (
    DpaeCorrelationDecision, DpaeDomainError,
    DpaeReturn, DpaeReturnEffect, DpaeReturnType,
)
from infrastructure.persistence.mysql_dpae_repository import MysqlDpaeRepository

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)

NOW = datetime(2026, 9, 27, 12, 0)


def connect():
    return mysql.connect(
        host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
        user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
        database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False,
    )


def repo():
    return MysqlDpaeRepository(connect)


def seed_case_submissions():
    conn = connect(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO tw_dpae_case (id,case_key,contract_id,status,origin,created_at) VALUES ('c1','case-1','ct1','IN_PROGRESS','TEAMWORKS',NOW())")
        cur.execute("INSERT INTO tw_dpae_snapshot (id,case_id,contract_id,rules_version,source_fingerprint,canonical_payload,payload_hash,created_at) VALUES ('snap1','c1','ct1','test-rules',%s,'{}',%s,NOW())", ("f" * 64, "a" * 64))
        for sid, attempt in (("s1", 1), ("s2", 2)):
            cur.execute("INSERT INTO tw_dpae_submission (id,case_id,snapshot_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES (%s,'c1','snap1',%s,%s,%s,'SENDING',NOW())", (sid, attempt, "cmd-" + sid, (sid * 64)[:64]))
        conn.commit()
    finally:
        cur.close(); conn.close()


def make_return(return_id="r1", external="ext-1", raw_hash="a" * 64):
    return DpaeReturn(id=return_id, provider="URSSAF", return_type=DpaeReturnType.RETURN_41,
                      raw_hash=raw_hash, received_at=NOW, external_return_id=external)


def test_adapter_ingest_replay_and_integrity_conflict(clean_tables):
    r = repo()
    created, state = r.ingest_return(make_return())
    assert (created.id, state) == ("r1", "CREATED")
    replay, state = r.ingest_return(make_return("r2"))
    assert (replay.id, state) == ("r1", "REPLAY")
    with pytest.raises(DpaeDomainError) as caught:
        r.ingest_return(make_return("r3", raw_hash="b" * 64))
    assert caught.value.code == "RETURN_INTEGRITY_CONFLICT"


def test_adapter_correlation_is_compare_and_swap(clean_tables):
    seed_case_submissions(); r = repo(); r.ingest_return(make_return())
    assert r.confirm_correlation("r1", "s1", "c1", 0) == "CONFIRMED"
    assert r.confirm_correlation("r1", "s1", "c1", 0) == "ALREADY_CONFIRMED"
    with pytest.raises(DpaeDomainError) as caught:
        r.confirm_correlation("r1", "s2", "c1", 0)
    assert caught.value.code == "DPAE_CORRELATION_STALE"


def test_adapter_current_correlation_constraint_survives_concurrency(clean_tables):
    seed_case_submissions(); r = repo(); r.ingest_return(make_return())
    assert r.confirm_correlation("r1", "s1", "c1", 0) == "CONFIRMED"

    def append(args):
        did, sid = args
        try:
            repo().append_decision(DpaeCorrelationDecision(
                id=did, return_id="r1", action="CONFIRM_MATCH", actor_id=did,
                decided_at=NOW, candidate_submission_id=sid))
            return "OK"
        except DpaeDomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(append, (("d1", "s1"), ("d2", "s2"))))
    assert results.count("OK") == 1
    assert "CONCURRENT_CORRELATION_CONFLICT" in results


def test_adapter_effect_requires_confirmation_and_is_exactly_once(clean_tables):
    seed_case_submissions(); r = repo(); r.ingest_return(make_return())
    effect = DpaeReturnEffect("r1", "MARK_DPAE_REGISTERED", NOW)
    with pytest.raises(DpaeDomainError) as caught:
        r.record_effect_once(effect)
    assert caught.value.code == "DPAE_UNCONFIRMED_RETURN_EFFECT"
    r.confirm_correlation("r1", "s1", "c1", 0)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: repo().record_effect_once(effect), range(2)))
    assert sorted(results) == [False, True]
    assert r.effect_count("r1", "MARK_DPAE_REGISTERED") == 1


def test_adapter_submission_lock_is_database_backed(clean_tables):
    seed_case_submissions()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda sid: repo().acquire_submission_lock("c1", sid, NOW), ("s1", "s2")))
    assert sorted(results) == [False, True]
