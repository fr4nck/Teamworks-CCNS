"""Real SQLite employee-edit transactions, optimistic concurrency and scope."""

import sqlite3
from types import SimpleNamespace

import pytest

from application.services.person_generalities_write import (
    PersonDetailsSnapshot,
    save_person_details,
    validate_person_details,
)
from infrastructure.persistence.person_generalities_write_adapter import (
    GestionDbPersonDetailsWriteAdapter,
)


class Database:
    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.echec = 0
        self.isNetwork = False
        self.closed = False
        self.cursor.executescript("""
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY,
                nom TEXT, prenom TEXT, adresse_resid TEXT,
                cp_resid INTEGER, ville_resid TEXT, memo TEXT,
                num_secu TEXT NOT NULL, date_naiss TEXT, IDsituation INTEGER
            );
            INSERT INTO personnes VALUES (
                12, 'DUPONT', 'Alice', 'Rue du stade', 3510,
                'Bais', 'Original', 'sensitive-value', '1990-02-03', 17
            );
        """)
        self.connexion.commit()

    def Close(self):
        self.closed = True
        self.connexion.close()


def next_details(current, **changes):
    existing = current.details
    data = dict(
        last_name=existing.last_name, first_name=existing.first_name,
        address=existing.address, postcode=str(existing.postcode).zfill(5)
        if existing.postcode is not None else "",
        city=existing.city, memo=existing.memo,
    )
    data.update(changes)
    return validate_person_details(**data)


def test_sqlite_roundtrip_persists_fields_without_touching_sensitive_columns():
    db = Database()
    port = GestionDbPersonDetailsWriteAdapter(db)
    try:
        snapshot = port.load(12)
        assert snapshot.details.postcode == 3510
        updated = next_details(
            snapshot, last_name="MARTIN", first_name="Élodie",
            address="4 avenue du sport", postcode="35000",
            city="Rennes", memo="Mise à jour",
        )
        result = save_person_details(port, snapshot, updated)
        assert result.ok and result.committed and result.verified
        assert port.load(12).details == updated
        assert db.connexion.execute(
            "SELECT num_secu, date_naiss, IDsituation FROM personnes"
        ).fetchone() == ("sensitive-value", "1990-02-03", 17)
        assert not db.connexion.in_transaction
    finally:
        port.close()
    assert db.closed


def test_stale_form_cannot_overwrite_other_users_changes():
    db = Database()
    port = GestionDbPersonDetailsWriteAdapter(db)
    try:
        initial = port.load(12)
        db.connexion.execute("UPDATE personnes SET memo='Concurrent' WHERE IDpersonne=12")
        db.connexion.commit()
        result = save_person_details(port, initial, next_details(initial, memo="Ancien formulaire"))
        assert result.code == "CONFLICT" and not result.committed
        assert db.connexion.execute("SELECT memo FROM personnes").fetchone() == ("Concurrent",)
    finally:
        port.close()


def test_sqlite_atomic_where_protects_change_between_read_and_update():
    db = Database()
    port = GestionDbPersonDetailsWriteAdapter(db)
    try:
        initial = port.load(12)
        updated = next_details(initial, memo="Changement A")
        db.connexion.execute("UPDATE personnes SET memo='Changement B' WHERE IDpersonne=12")
        assert port.update_if_unchanged(initial, updated) == 0
        db.connexion.rollback()
    finally:
        port.close()


def test_missing_id_and_invalid_connection_fail_closed():
    db = Database()
    port = GestionDbPersonDetailsWriteAdapter(db)
    try:
        assert port.load(99999) is None
        with pytest.raises(ValueError, match="Identifiant"):
            port.load(True)
    finally:
        port.close()
    with pytest.raises(RuntimeError, match="indisponible"):
        GestionDbPersonDetailsWriteAdapter(SimpleNamespace(echec=1))


def test_mysql_uses_null_safe_bound_parameters_instead_of_string_formatting():
    observed = []

    class Cursor:
        rowcount = 1
        def execute(self, sql, params):
            observed.append((sql, params))
        def fetchone(self):
            return ("DUPONT", "Alice", None, 3510, "Bais", None)

    fake = SimpleNamespace(
        echec=0, isNetwork=True,
        cursor=Cursor(), connexion=SimpleNamespace(),
    )
    port = GestionDbPersonDetailsWriteAdapter(fake)
    before = port.load(12)
    assert before is not None
    updated = next_details(before, memo="Mise à jour")
    assert port.update_if_unchanged(before, updated) == 1
    sql, params = observed[-1]
    assert sql.count("<=> %s") == 6
    assert "WHERE IDpersonne=%s" in sql
    assert "Mise à jour" not in sql
    assert "memo" in sql
    assert params[-6:] == (
        "DUPONT", "Alice", None, 3510, "Bais", None
    )


def test_sqlite_user_can_clear_optional_fields_without_replacing_null_with_dash():
    db = Database()
    port = GestionDbPersonDetailsWriteAdapter(db)
    try:
        current = port.load(12)
        result = save_person_details(
            port, current, next_details(
                current, address="", postcode="", city="", memo="",
            )
        )
        assert result.ok
        assert db.connexion.execute(
            "SELECT adresse_resid,cp_resid,ville_resid,memo FROM personnes"
        ).fetchone() == (None, None, None, None)
    finally:
        port.close()
