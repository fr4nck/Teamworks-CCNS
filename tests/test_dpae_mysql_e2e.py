"""E2E MariaDB via le vrai DpaeService, resolver Teamworks et adaptateur DPAE."""
import hashlib
import json
import os
from datetime import datetime

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import (
    DpaeService, IngestDpaeReturn, PrepareDpae, RetryDpaeSubmission,
    SubmitDpae, TransmissionResult,
)
from infrastructure.dpae_teamworks_resolver import TeamworksDpaeBusinessDataResolver
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED): pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)


def connect():
    return mysql.connect(host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")), user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""), database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False)


def install_teamworks_fixture():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS contrats (IDcontrat INT PRIMARY KEY, IDpersonne INT, IDtype INT, IDclassification INT, date_debut DATE, date_fin DATE, essai INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS personnes (IDpersonne INT PRIMARY KEY, civilite VARCHAR(16), nom VARCHAR(80), nom_jfille VARCHAR(80), prenom VARCHAR(80), date_naiss DATE, cp_naiss VARCHAR(16), ville_naiss VARCHAR(80), nationalite INT, num_secu VARCHAR(32), adresse_resid VARCHAR(160), cp_resid VARCHAR(16), ville_resid VARCHAR(80), pays_naiss INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS contrats_types (IDtype INT PRIMARY KEY, nom VARCHAR(80), nom_abrege VARCHAR(32), duree_indeterminee VARCHAR(16))")
        cur.execute("CREATE TABLE IF NOT EXISTS contrats_class (IDclassification INT PRIMARY KEY, nom VARCHAR(80))")
        cur.execute("CREATE TABLE IF NOT EXISTS pays (IDpays INT PRIMARY KEY, nom VARCHAR(80), nationalite VARCHAR(80))")
        for table in ("contrats", "personnes", "contrats_types", "contrats_class", "pays"): cur.execute("DELETE FROM " + table)
        cur.execute("INSERT INTO pays VALUES (33,'France','Française')"); cur.execute("INSERT INTO contrats_types VALUES (2,'CDD','CDD','non')"); cur.execute("INSERT INTO contrats_class VALUES (3,'Groupe B')")
        cur.execute("INSERT INTO personnes VALUES (18,'Mme','Martin','Durand','Alice','1990-02-03','35000','Rennes',33,'','1 rue X','35650','Le Rheu',33)")
        cur.execute("INSERT INTO contrats VALUES (742,18,2,3,'2026-10-15','2027-10-14',7)"); conn.commit()
    finally: conn.close()


def organisation_file(path):
    path.write_text("[organisation]\nnom_officiel=Association Test\nsiret=12345678901234\nsiren=123456789\nape_naf=9499Z\nadresse=2 rue Y\ncode_postal=35650\nville=Le Rheu\n", encoding="utf-8")


def rh_state():
    conn=connect()
    try:
        cur=conn.cursor(); state={}
        for table in ("contrats","personnes","contrats_types","contrats_class","pays"):
            cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",(table,)); cols=tuple(r[0] for r in cur.fetchall())
            cur.execute("SELECT * FROM " + table); rows=tuple(cur.fetchall()); state[table]=(cols,rows)
        return state
    finally: conn.close()


class FlakyTransport:
    def __init__(self): self.calls=[]
    def send(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls)==1: raise TimeoutError("lost ACK")
        return TransmissionResult("SENT", external_flux_id="flux-e2e-1")


def test_full_v2_chain_uses_real_teamworks_resolver_and_durable_snapshot(clean_tables, tmp_path):
    install_teamworks_fixture(); customize=tmp_path/"Customize.ini"; organisation_file(customize); before_config=customize.read_bytes(); before_rh=rh_state()
    adapter=DpaeMariaDbAdapter(connect); resolver=TeamworksDpaeBusinessDataResolver(connect, customize); service=DpaeService(adapter, resolver=resolver)
    prepared=service.prepare(PrepareDpae("e2e-prepare-v2","contract-742","742","operator")); submitted=service.submit(SubmitDpae("e2e-submit-v2",prepared["case_id"],"operator"))
    assert prepared["snapshot_id"]==submitted["snapshot_id"]; assert prepared["payload_hash"]==submitted["payload_hash"]; assert customize.read_bytes()==before_config; assert rh_state()==before_rh
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute("SELECT contract_id FROM tw_dpae_case WHERE id=%s",(prepared["case_id"],)); assert str(cur.fetchone()[0])=="742"
        cur.execute("SELECT canonical_payload FROM tw_dpae_snapshot WHERE id=%s",(prepared["snapshot_id"],)); payload=json.loads(cur.fetchone()[0]); assert payload["employee"]["birth_name"]=="Durand"; assert "person_id" not in payload["employee"]; assert payload["contract"]["hiring_time"] is None
        cur.execute("SELECT snapshot_id FROM tw_dpae_submission WHERE id=%s",(submitted["submission_id"],)); assert cur.fetchone()[0]==prepared["snapshot_id"]
    finally: conn.close()


def test_real_teamworks_change_creates_s2_without_mutating_s1(clean_tables,tmp_path):
    install_teamworks_fixture(); customize=tmp_path/"Customize.ini"; organisation_file(customize); service=DpaeService(DpaeMariaDbAdapter(connect),resolver=TeamworksDpaeBusinessDataResolver(connect,customize))
    s1=service.prepare(PrepareDpae("s1-command","contract-742-v1","742","operator"))
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute("SELECT canonical_payload,source_fingerprint,payload_hash FROM tw_dpae_snapshot WHERE id=%s",(s1["snapshot_id"],)); before=cur.fetchone(); cur.execute("UPDATE personnes SET prenom='Alicia' WHERE IDpersonne=18"); conn.commit()
    finally: conn.close()
    s2=service.prepare(PrepareDpae("s2-command","contract-742-v2","742","operator")); assert s1["snapshot_id"]!=s2["snapshot_id"]
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute("SELECT canonical_payload,source_fingerprint,payload_hash FROM tw_dpae_snapshot WHERE id=%s",(s1["snapshot_id"],)); assert cur.fetchone()==before
        cur.execute("SELECT canonical_payload,source_fingerprint,payload_hash FROM tw_dpae_snapshot WHERE id=%s",(s2["snapshot_id"],)); after=cur.fetchone(); assert json.loads(before[0])["employee"]["first_names"]=="Alice"; assert json.loads(after[0])["employee"]["first_names"]=="Alicia"; assert before[1]!=after[1]; assert before[2]!=after[2]
    finally: conn.close()


def test_retry_and_return_keep_historical_snapshot_after_rh_change(clean_tables,tmp_path):
    install_teamworks_fixture(); customize=tmp_path/"Customize.ini"; organisation_file(customize); transport=FlakyTransport(); adapter=DpaeMariaDbAdapter(connect); resolver=TeamworksDpaeBusinessDataResolver(connect,customize); service=DpaeService(adapter,transport=transport,resolver=resolver)
    prepared=service.prepare(PrepareDpae("retry-prepare","contract-retry-742","742","operator"))
    with pytest.raises(TimeoutError): service.submit(SubmitDpae("retry-submit",prepared["case_id"],"operator"))
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute("UPDATE personnes SET prenom='Alicia' WHERE IDpersonne=18"); conn.commit()
    finally: conn.close()
    retried=service.retry_submission(RetryDpaeSubmission(transport.calls[0]["submission_id"])); assert retried["snapshot_id"]==prepared["snapshot_id"]; assert retried["payload_hash"]==prepared["payload_hash"]; assert retried["attempt_no"]==1
    assert transport.calls[0]["canonical_payload"]==transport.calls[1]["canonical_payload"]
    returned=service.ingest_return(IngestDpaeReturn(provider="URSSAF",return_type="AEE",raw_hash=hashlib.sha256(b"return-1").hexdigest(),received_at=datetime(2026,9,27,12,0),external_return_id="return-e2e-1",external_flux_id="flux-e2e-1",employer_siret="12345678901234")); assert returned["correlation_status"]=="MATCHED"
    evidence=adapter.get_historical_evidence(returned["return_id"]); assert evidence["submission_id"]==retried["submission_id"]; assert evidence["snapshot_id"]==prepared["snapshot_id"]; assert evidence["contract_id"]=="742"; assert evidence["canonical_payload"]==transport.calls[0]["canonical_payload"]
