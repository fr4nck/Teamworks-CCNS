"""Régressions MariaDB V2 autour des conflits/replays d'idempotence."""
import os
import pytest
mysql=pytest.importorskip("mysql.connector")
if not all(os.getenv(n) for n in ("DPAE_MYSQL_HOST","DPAE_MYSQL_USER","DPAE_MYSQL_DATABASE")): pytest.skip("base MySQL DPAE non configurée",allow_module_level=True)

from application.services.dpae_service import DpaeBusinessData,DpaeService,PrepareDpae
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter,IdempotencyPayloadConflict


def connect(): return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"],port=int(os.getenv("DPAE_MYSQL_PORT","3306")),user=os.environ["DPAE_MYSQL_USER"],password=os.getenv("DPAE_MYSQL_PASSWORD",""),database=os.environ["DPAE_MYSQL_DATABASE"],use_pure=True,autocommit=False)


class Resolver:
    def __init__(self): self.calls=0
    def resolve(self,contract_id): self.calls+=1; return DpaeBusinessData(contract_id,'{"contract":"'+contract_id+'"}',"f"*64,"test-rules","a"*64)


def durable(command_id):
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute("SELECT command_hash,decision,case_id FROM tw_dpae_command_audit WHERE command_id=%s",(command_id,)); audit=cur.fetchone(); cur.execute("SELECT COUNT(*) FROM tw_dpae_snapshot"); snaps=cur.fetchone()[0]; cur.execute("SELECT COUNT(*) FROM tw_dpae_case"); cases=cur.fetchone()[0]; return audit,snaps,cases
    finally: conn.close()


def test_conflict_then_reconnect_keeps_original_durable_state(clean_tables):
    resolver=Resolver(); command_id="conflict-reconnect-command"; first=DpaeService(DpaeMariaDbAdapter(connect),resolver=resolver); result=first.prepare(PrepareDpae(command_id,"case-one","contract-one","operator")); before=durable(command_id)
    restarted=DpaeService(DpaeMariaDbAdapter(connect),resolver=resolver)
    with pytest.raises(IdempotencyPayloadConflict,match="IDEMPOTENCY_PAYLOAD_CONFLICT"): restarted.prepare(PrepareDpae(command_id,"case-two","contract-two","operator"))
    assert resolver.calls==1; assert durable(command_id)==before; assert before[1:]==(1,1); assert before[0][2]==result["case_id"]


def test_exact_replay_after_restart_recovers_without_resolver_or_duplicate(clean_tables):
    resolver=Resolver(); command=PrepareDpae("restart-replay","case-replay","contract-replay","operator"); first=DpaeService(DpaeMariaDbAdapter(connect),resolver=resolver); original=first.prepare(command); before=durable(command.command_id)
    restarted=DpaeService(DpaeMariaDbAdapter(connect),resolver=resolver); replay=restarted.prepare(command)
    assert resolver.calls==1; assert replay["replayed"] is True; assert replay["case_id"]==original["case_id"]; assert replay["snapshot_id"]==original["snapshot_id"]; assert durable(command.command_id)==before
