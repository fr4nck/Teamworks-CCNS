"""Garanties transactionnelles DPAE V2 sur une vraie base MySQL/MariaDB."""
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

mysql=pytest.importorskip("mysql.connector")
REQUIRED=("DPAE_MYSQL_HOST","DPAE_MYSQL_USER","DPAE_MYSQL_DATABASE")
if not all(os.getenv(n) for n in REQUIRED): pytest.skip("base MySQL DPAE de recette non configurée",allow_module_level=True)


def connect(): return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"],port=int(os.getenv("DPAE_MYSQL_PORT","3306")),user=os.environ["DPAE_MYSQL_USER"],password=os.getenv("DPAE_MYSQL_PASSWORD",""),database=os.environ["DPAE_MYSQL_DATABASE"],use_pure=True,autocommit=False)


def seed_case_submission_return():
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute("INSERT INTO tw_dpae_case (id,case_key,contract_id,status,origin,created_at,version) VALUES ('c1','case-1','ct1','SUBMITTING','TEAMWORKS',NOW(),1)")
        for sid,attempt in (("s1",1),("s2",2)):
            snap="p"+sid; payload=(sid*32)[:64]; cur.execute("INSERT INTO tw_dpae_snapshot (id,case_id,contract_id,rules_version,source_fingerprint,canonical_payload,payload_hash,created_at) VALUES (%s,'c1','ct1','test-v2',%s,%s,%s,NOW())",(snap,"f"*64,'{"test":"'+sid+'"}',payload)); cur.execute("INSERT INTO tw_dpae_submission (id,case_id,snapshot_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES (%s,'c1',%s,%s,%s,%s,'SENDING',NOW())",(sid,snap,attempt,"cmd-"+sid,payload))
        cur.execute("INSERT INTO tw_dpae_return (id,provider,return_type,raw_hash,received_at,external_return_id,correlation_status,processing_status,version) VALUES ('r1','URSSAF','RETURN_41',%s,NOW(),'ext-1','UNMATCHED','PROCESSED',1)",("a"*64,)); conn.commit()
    finally: conn.close()


def test_unique_case_key_and_submission_idempotency_are_enforced_by_mysql(clean_tables):
    seed_case_submission_return(); conn=connect()
    try:
        cur=conn.cursor()
        with pytest.raises(mysql.IntegrityError): cur.execute("INSERT INTO tw_dpae_case (id,case_key,contract_id,status,origin,created_at) VALUES ('cx','case-1','ct2','READY','TEAMWORKS',NOW())")
        conn.rollback()
        with pytest.raises(mysql.IntegrityError): cur.execute("INSERT INTO tw_dpae_submission (id,case_id,snapshot_id,attempt_no,idempotency_key,payload_hash,state,created_at) VALUES ('sx','c1','ps1',3,'cmd-s1',%s,'PREPARED',NOW())",("b"*64,))
    finally: conn.close()


def test_two_workers_cannot_hold_uncertain_submission_lock_for_same_case(clean_tables):
    seed_case_submission_return()
    def acquire(sid):
        conn=connect()
        try:
            cur=conn.cursor()
            try: cur.execute("INSERT INTO tw_dpae_case_submission_lock (case_id,submission_id,acquired_at) VALUES ('c1',%s,NOW())",(sid,)); conn.commit(); return "ACQUIRED"
            except mysql.IntegrityError: conn.rollback(); return "CONFLICT"
        finally: conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(acquire,("s1","s2")))
    assert sorted(results)==["ACQUIRED","CONFLICT"]


def test_two_operators_cannot_create_two_current_correlations(clean_tables):
    seed_case_submission_return()
    def confirm(args):
        did,sid=args; conn=connect()
        try:
            cur=conn.cursor()
            try:
                cur.execute("INSERT INTO tw_dpae_correlation_decision (id,return_id,action,actor_id,decided_at,candidate_submission_id) VALUES (%s,'r1','CONFIRM_MATCH',%s,NOW(),%s)",(did,did,sid)); cur.execute("INSERT INTO tw_dpae_current_correlation (return_id,submission_id,decision_id,confirmed_at) VALUES ('r1',%s,%s,NOW())",(sid,did)); conn.commit(); return "CONFIRMED"
            except mysql.IntegrityError: conn.rollback(); return "CONFLICT"
        finally: conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(confirm,(("d1","s1"),("d2","s2"))))
    assert sorted(results)==["CONFIRMED","CONFLICT"]


def test_return_effect_is_exactly_once_under_concurrency(clean_tables):
    seed_case_submission_return()
    def apply(_):
        conn=connect()
        try:
            cur=conn.cursor()
            try: cur.execute("INSERT INTO tw_dpae_return_effect (return_id,effect_type,created_at) VALUES ('r1','MARK_DPAE_REGISTERED',NOW())"); conn.commit(); return "CREATED"
            except mysql.IntegrityError: conn.rollback(); return "REPLAY"
        finally: conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(apply,range(2)))
    assert sorted(results)==["CREATED","REPLAY"]
