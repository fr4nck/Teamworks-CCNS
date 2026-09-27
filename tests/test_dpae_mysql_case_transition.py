"""Intégration de la machine DpaeCase avec MySQL/MariaDB réel."""
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

mysql = pytest.importorskip("mysql.connector")
if not all(os.getenv(k) for k in ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")):
    pytest.skip("base MySQL DPAE non configurée", allow_module_level=True)

from domain.dpae.case_transition import DpaeCapability, DpaeCaseEvent, TransitionContext
from domain.dpae.model import DpaeCaseStatus, DpaeDomainError
from infrastructure.persistence.mysql_dpae_repository import MysqlDpaeRepository


def connect():
    return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
                         user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
                         database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False)


def seed_case(status="DRAFT", version=0):
    conn=connect(); cur=conn.cursor()
    try:
        cur.execute("INSERT INTO tw_dpae_case (id,case_key,contract_id,status,origin,created_at,version) VALUES ('c1','case-key','ct1',%s,'TEAMWORKS',NOW(),%s)",(status,version)); conn.commit()
    finally: cur.close(); conn.close()


def ctx(version=0, caps=frozenset({DpaeCapability.PREPARE}), **kwargs):
    return TransitionContext(actor_id="tester", capabilities=caps, expected_version=version, **kwargs)


def test_transition_is_persisted_with_version(clean_tables):
    seed_case(); repo=MysqlDpaeRepository(connect)
    result=repo.transition_case("c1",DpaeCaseEvent.CONTRACT_READY,ctx())
    assert result.status is DpaeCaseStatus.TO_VALIDATE
    assert result.version==1
    persisted=repo.get_case("c1")
    assert persisted.status is DpaeCaseStatus.TO_VALIDATE
    assert persisted.version==1


def test_failed_guard_rolls_back_without_changing_case(clean_tables):
    seed_case(); repo=MysqlDpaeRepository(connect)
    with pytest.raises(DpaeDomainError) as caught:
        repo.transition_case("c1",DpaeCaseEvent.CONTRACT_READY,ctx(contract_complete=False))
    assert caught.value.code=="DPAE-P001"
    persisted=repo.get_case("c1")
    assert persisted.status is DpaeCaseStatus.DRAFT and persisted.version==0


def test_two_operators_with_same_version_only_one_transition_wins(clean_tables):
    seed_case(); repo=MysqlDpaeRepository(connect)
    def worker():
        try:
            value=repo.transition_case("c1",DpaeCaseEvent.CONTRACT_READY,ctx())
            return ("OK",value.status.value,value.version)
        except DpaeDomainError as exc:
            return ("ERR",exc.code)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=[f.result(timeout=10) for f in (pool.submit(worker),pool.submit(worker))]
    assert sum(r[0]=="OK" for r in results)==1
    assert [r for r in results if r[0]=="ERR"][0][1] in {"DPAE-I010","DPAE-T001"}
    persisted=repo.get_case("c1")
    assert persisted.status is DpaeCaseStatus.TO_VALIDATE and persisted.version==1


def test_stale_expected_version_does_not_mutate_database(clean_tables):
    seed_case(version=4); repo=MysqlDpaeRepository(connect)
    with pytest.raises(DpaeDomainError) as caught:
        repo.transition_case("c1",DpaeCaseEvent.CONTRACT_READY,ctx(version=3))
    assert caught.value.code=="DPAE-I010"
    persisted=repo.get_case("c1")
    assert persisted.status is DpaeCaseStatus.DRAFT and persisted.version==4


def test_cancel_sets_closed_at_and_is_atomic(clean_tables):
    seed_case(); repo=MysqlDpaeRepository(connect)
    result=repo.transition_case("c1",DpaeCaseEvent.CANCEL_CASE,ctx(reason_code="CONTRACT_CANCELLED"))
    assert result.status is DpaeCaseStatus.CANCELLED
    assert result.closed_at is not None
    persisted=repo.get_case("c1")
    assert persisted.closed_at is not None and persisted.version==1
