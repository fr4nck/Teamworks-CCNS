"""E2E MariaDB via le vrai DpaeService, resolver Teamworks et adaptateur DPAE."""
import json
import os

import pytest

mysql = pytest.importorskip("mysql.connector")

from application.services.dpae_service import DpaeService, PrepareDpae, SubmitDpae
from infrastructure.dpae_teamworks_resolver import TeamworksDpaeBusinessDataResolver
from infrastructure.persistence.dpae_mysql import DpaeMariaDbAdapter

REQUIRED = ("DPAE_MYSQL_HOST", "DPAE_MYSQL_USER", "DPAE_MYSQL_DATABASE")
if not all(os.getenv(name) for name in REQUIRED):
    pytest.skip("base MySQL DPAE de recette non configurée", allow_module_level=True)


def connect():
    return mysql.connect(
        host=os.environ["DPAE_MYSQL_HOST"], port=int(os.getenv("DPAE_MYSQL_PORT", "3306")),
        user=os.environ["DPAE_MYSQL_USER"], password=os.getenv("DPAE_MYSQL_PASSWORD", ""),
        database=os.environ["DPAE_MYSQL_DATABASE"], use_pure=True, autocommit=False,
    )


def install_teamworks_fixture():
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS contrats (IDcontrat INT PRIMARY KEY, IDpersonne INT, IDtype INT, IDclassification INT, date_debut DATE, date_fin DATE, essai INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS personnes (IDpersonne INT PRIMARY KEY, civilite VARCHAR(16), nom VARCHAR(80), nom_jfille VARCHAR(80), prenom VARCHAR(80), date_naiss DATE, cp_naiss VARCHAR(16), ville_naiss VARCHAR(80), nationalite INT, num_secu VARCHAR(32), adresse_resid VARCHAR(160), cp_resid VARCHAR(16), ville_resid VARCHAR(80), pays_naiss INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS contrats_types (IDtype INT PRIMARY KEY, nom VARCHAR(80), nom_abrege VARCHAR(32), duree_indeterminee VARCHAR(16))")
        cur.execute("CREATE TABLE IF NOT EXISTS contrats_class (IDclassification INT PRIMARY KEY, nom VARCHAR(80))")
        cur.execute("CREATE TABLE IF NOT EXISTS pays (IDpays INT PRIMARY KEY, nom VARCHAR(80), nationalite VARCHAR(80))")
        for table in ("contrats", "personnes", "contrats_types", "contrats_class", "pays"):
            cur.execute("DELETE FROM " + table)
        cur.execute("INSERT INTO pays VALUES (33,'France','Française')")
        cur.execute("INSERT INTO contrats_types VALUES (2,'CDD','CDD','non')")
        cur.execute("INSERT INTO contrats_class VALUES (3,'Groupe B')")
        cur.execute("INSERT INTO personnes VALUES (18,'Mme','Martin','Durand','Alice','1990-02-03','35000','Rennes',33,'','1 rue X','35650','Le Rheu',33)")
        cur.execute("INSERT INTO contrats VALUES (742,18,2,3,'2026-10-15','2027-10-14',7)")
        conn.commit()
    finally:
        conn.close()


def test_full_v2_chain_uses_real_teamworks_resolver_and_durable_snapshot(clean_tables, tmp_path):
    install_teamworks_fixture()
    customize = tmp_path / "Customize.ini"
    customize.write_text(
        "[organisation]\nnom_officiel=Association Test\nsiret=12345678901234\n"
        "siren=123456789\nape_naf=9499Z\nadresse=2 rue Y\ncode_postal=35650\nville=Le Rheu\n",
        encoding="utf-8",
    )
    before_config = customize.read_bytes()
    adapter = DpaeMariaDbAdapter(connect)
    resolver = TeamworksDpaeBusinessDataResolver(connect, customize)
    service = DpaeService(adapter, resolver=resolver)

    prepared = service.prepare(PrepareDpae("e2e-prepare-v2", "contract-742", "742", "operator"))
    submitted = service.submit(SubmitDpae("e2e-submit-v2", prepared["case_id"], "operator"))

    assert prepared["snapshot_id"] == submitted["snapshot_id"]
    assert prepared["payload_hash"] == submitted["payload_hash"]
    assert customize.read_bytes() == before_config

    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT contract_id FROM tw_dpae_case WHERE id=%s", (prepared["case_id"],))
        assert str(cur.fetchone()[0]) == "742"
        cur.execute("SELECT canonical_payload FROM tw_dpae_snapshot WHERE id=%s", (prepared["snapshot_id"],))
        payload = json.loads(cur.fetchone()[0])
        assert payload["employee"]["birth_name"] == "Durand"
        assert "person_id" not in payload["employee"]
        assert payload["contract"]["hiring_time"] is None
        cur.execute("SELECT snapshot_id FROM tw_dpae_submission WHERE id=%s", (submitted["submission_id"],))
        assert cur.fetchone()[0] == prepared["snapshot_id"]
    finally:
        conn.close()
