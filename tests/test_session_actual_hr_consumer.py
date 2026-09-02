from __future__ import annotations

from datetime import datetime
import sqlite3

import pytest

from application.services.session_actual_hr import SessionActualHrConsumer
from domain.employment import SessionActual, SessionActualContractError
from infrastructure.persistence.session_actual_hr_repository import (
    INBOX_TABLE,
    MAPPING_TABLE,
    WORK_TABLE,
    SessionActualHrPersistenceError,
    SessionActualHrRepository,
)


class SQLiteTestDB:
    isNetwork = False

    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.cursor.execute(
            "CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, nom TEXT, prenom TEXT)"
        )
        self.cursor.execute(
            "CREATE TABLE contrats (IDcontrat INTEGER PRIMARY KEY, IDpersonne INTEGER, marqueur TEXT)"
        )
        self.cursor.execute(
            "CREATE TABLE assignments (id INTEGER PRIMARY KEY, person_id INTEGER, marqueur TEXT)"
        )
        self.cursor.execute(
            "CREATE TABLE tw_payroll_sentinel (id INTEGER PRIMARY KEY, marqueur TEXT)"
        )
        self.cursor.execute("INSERT INTO contrats VALUES (1, 1, 'contrat-intact')")
        self.cursor.execute("INSERT INTO assignments VALUES (1, 1, 'planning-intact')")
        self.cursor.execute("INSERT INTO tw_payroll_sentinel VALUES (1, 'paie-intacte')")
        self.connexion.commit()

    def IsTableExists(self, table_name):
        row = self.connexion.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
        ).fetchone()
        return row is not None

    def Commit(self):
        self.connexion.commit()

    def Rollback(self):
        self.connexion.rollback()

    def Close(self):
        self.connexion.close()


def payload(**overrides):
    data = {
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "actual_uuid": "ACT-001",
        "actual_revision": 1,
        "session_uid": "INT-SESSION-001",
        "session_status": "realisee",
        "assignment_date": "2026-09-02",
        "validated_at": "2026-09-02T08:20:00+02:00",
        "actual_staff_uid": "EMP-UID-001",
        "actual_place_uid": "PLACE-UID-001",
        "actual_start_time": "09:00",
        "actual_end_time": "10:30",
        "actual_duration_minutes": 90,
        "actual_comment": "Séance réalisée",
    }
    data.update(overrides)
    return data


def cancelled_payload(**overrides):
    data = payload(
        session_status="annulee",
        actual_staff_uid=None,
        actual_place_uid=None,
        actual_start_time=None,
        actual_end_time=None,
        actual_duration_minutes=None,
        actual_comment="Séance annulée par le responsable",
    )
    data.update(overrides)
    return data


def ready_repository():
    db = SQLiteTestDB()
    repository = SessionActualHrRepository(db_factory=lambda: db)
    assert set(repository.ensure_schema()) == {MAPPING_TABLE, INBOX_TABLE, WORK_TABLE}
    assert repository.ensure_schema(apply=True) == ()
    db.cursor.execute("INSERT INTO personnes VALUES (1, 'Lovelace', 'Ada')")
    db.cursor.execute("INSERT INTO personnes VALUES (2, 'Hopper', 'Grace')")
    db.Commit()
    repository.register_person_uid("EMP-UID-001", 1)
    repository.register_person_uid("EMP-UID-002", 2)
    return db, repository


def test_contrat_session_actual_1_est_aligne_sur_le_producteur():
    actual = SessionActual.from_payload(payload())

    assert actual.session_uid == "INT-SESSION-001"
    assert actual.actual_staff_uid == "EMP-UID-001"
    assert actual.actual_duration_minutes == 90
    assert actual.canonical_payload() == payload()
    assert len(actual.payload_sha256()) == 64


def test_contrat_refuse_duree_incoherente_et_annulation_avec_intervenant():
    with pytest.raises(SessionActualContractError, match="durée réelle incohérente"):
        SessionActual.from_payload(payload(actual_duration_minutes=91))

    with pytest.raises(SessionActualContractError, match="séance annulée"):
        SessionActual.from_payload(cancelled_payload(actual_staff_uid="EMP-UID-001"))


def test_schema_est_additif_explicite_et_idempotent():
    db = SQLiteTestDB()
    repository = SessionActualHrRepository(db_factory=lambda: db)

    assert not db.IsTableExists(MAPPING_TABLE)
    assert repository.ensure_schema(apply=False)
    assert not db.IsTableExists(MAPPING_TABLE)
    assert repository.ensure_schema(apply=True) == ()
    assert repository.ensure_schema(apply=True) == ()


def test_schema_mysql_utilise_auto_increment_sans_sqlite_autoincrement():
    mysql_sql = "\n".join(SessionActualHrRepository._schema_statements(True))
    sqlite_sql = "\n".join(SessionActualHrRepository._schema_statements(False))

    assert "AUTO_INCREMENT" in mysql_sql
    assert "AUTOINCREMENT" not in mysql_sql
    assert "AUTOINCREMENT" in sqlite_sql


def test_mapping_uid_exige_une_personne_existante_et_ne_cree_rien():
    db = SQLiteTestDB()
    repository = SessionActualHrRepository(db_factory=lambda: db)
    repository.ensure_schema(apply=True)

    with pytest.raises(SessionActualHrPersistenceError, match="Personne Teamworks introuvable"):
        repository.register_person_uid("EMP-UNKNOWN", 999)

    assert db.cursor.execute("SELECT COUNT(*) FROM personnes").fetchone()[0] == 0
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {MAPPING_TABLE}").fetchone()[0] == 0


def test_realise_est_applique_une_fois_sans_effet_planning_contrat_ou_paie():
    db, repository = ready_repository()
    consumer = SessionActualHrConsumer(repository)

    first = consumer.receive(
        payload(),
        idempotence_key="idem-001",
        received_at=datetime(2026, 9, 2, 8, 21, 0),
    )
    replay = consumer.receive(payload(), idempotence_key="idem-001")

    assert first.status == "applied"
    assert first.person_id == 1
    assert replay.status == "replayed"
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {WORK_TABLE}").fetchone()[0] == 1
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 1
    work = db.cursor.execute(
        f"SELECT session_uid, IDpersonne, actual_duration_minutes, actual_place_uid FROM {WORK_TABLE}"
    ).fetchone()
    assert work == ("INT-SESSION-001", 1, 90, "PLACE-UID-001")
    assert db.cursor.execute("SELECT marqueur FROM contrats").fetchone()[0] == "contrat-intact"
    assert db.cursor.execute("SELECT marqueur FROM assignments").fetchone()[0] == "planning-intact"
    assert db.cursor.execute("SELECT marqueur FROM tw_payroll_sentinel").fetchone()[0] == "paie-intacte"


def test_uid_salarie_inconnu_est_refuse_sans_ecriture_metier():
    db, repository = ready_repository()

    with pytest.raises(SessionActualHrPersistenceError, match="UID RH inconnu"):
        repository.receive(payload(actual_staff_uid="EMP-ABSENT"), "idem-unknown")

    assert db.cursor.execute(f"SELECT COUNT(*) FROM {WORK_TABLE}").fetchone()[0] == 0
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 0


def test_meme_revision_payload_different_est_un_conflit():
    db, repository = ready_repository()
    repository.receive(payload(), "idem-001")

    with pytest.raises(SessionActualHrPersistenceError, match="révision déjà reçue"):
        repository.receive(payload(actual_comment="Correction divergente"), "idem-002")

    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 1


def test_revision_plus_recente_met_a_jour_et_revision_ancienne_est_refusee():
    db, repository = ready_repository()
    repository.receive(payload(), "idem-001")
    corrected = payload(
        actual_revision=2,
        actual_staff_uid="EMP-UID-002",
        actual_start_time="09:15",
        actual_end_time="10:45",
        actual_duration_minutes=90,
        actual_comment="Correction validée",
    )

    result = repository.receive(corrected, "idem-002")
    assert result.status == "applied"
    assert result.person_id == 2
    assert db.cursor.execute(
        f"SELECT IDpersonne, actual_revision, actual_start_time FROM {WORK_TABLE}"
    ).fetchone() == (2, 2, "09:15")

    with pytest.raises(SessionActualHrPersistenceError, match="obsolète"):
        repository.receive(payload(), "idem-old")


def test_annulation_revisionnee_efface_le_realise_sans_supprimer_sa_trace_rh():
    db, repository = ready_repository()
    repository.receive(payload(), "idem-001")
    cancelled = cancelled_payload(actual_revision=2)

    result = repository.receive(cancelled, "idem-002")

    assert result.status == "applied"
    row = db.cursor.execute(
        f"""SELECT IDpersonne, actual_staff_uid, session_status,
            actual_start_time, actual_duration_minutes, actual_comment
            FROM {WORK_TABLE}"""
    ).fetchone()
    assert row == (1, None, "annulee", None, None, "Séance annulée par le responsable")
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 2


def test_domaine_source_incorrect_est_refuse():
    _, repository = ready_repository()

    with pytest.raises(SessionActualHrPersistenceError, match="domaine source non supporté"):
        repository.receive(payload(), "idem-001", source_domain="nom-produit-variable")


class FailingInboxRepository(SessionActualHrRepository):
    def _execute(self, sql, params=()):
        if sql.lstrip().startswith(f"INSERT INTO {INBOX_TABLE}"):
            raise RuntimeError("panne simulée après écriture du journal")
        return super()._execute(sql, params)


def test_panne_apres_ecriture_du_journal_declenche_un_rollback_atomique():
    db = SQLiteTestDB()
    repository = FailingInboxRepository(db_factory=lambda: db)
    repository.ensure_schema(apply=True)
    db.cursor.execute("INSERT INTO personnes VALUES (1, 'Lovelace', 'Ada')")
    db.Commit()
    repository.register_person_uid("EMP-UID-001", 1)

    with pytest.raises(RuntimeError, match="panne simulée"):
        repository.receive(payload(), "idem-001")

    assert db.cursor.execute(f"SELECT COUNT(*) FROM {WORK_TABLE}").fetchone()[0] == 0
    assert db.cursor.execute(f"SELECT COUNT(*) FROM {INBOX_TABLE}").fetchone()[0] == 0
