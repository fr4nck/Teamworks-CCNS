"""Intégration MariaDB : conflit d'idempotence V2 avant toute mutation."""
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


def counts():
    conn=connect()
    try:
        cur=conn.cursor(); out=[]
        for table in ("tw_dpae_case","tw_dpae_snapshot","tw_dpae_command_audit","tw_dpae_case_event","tw_dpae_submission"):
            cur.execute("SELECT COUNT(*) FROM "+table); out.append(cur.fetchone()[0])
        return tuple(out)
    finally: conn.close()


def test_same_command_id_with_different_logical_prepare_is_rejected_before_resolver_or_mutation(clean_tables):
    resolver=Resolver(); service=DpaeService(DpaeMariaDbAdapter(connect),resolver=resolver)
    service.prepare(PrepareDpae("cmd-payload-conflict","case-c1","contract-c1","operator")); assert resolver.calls==1; before=counts()
    with pytest.raises(IdempotencyPayloadConflict,match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        service.prepare(PrepareDpae("cmd-payload-conflict","case-c2","contract-c2","operator"))
    assert resolver.calls==1; assert counts()==before
