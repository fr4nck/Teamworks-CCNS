"""Round-trips SQLite du contrat transactionnel Frais / remboursements."""

from __future__ import annotations

import sqlite3
from datetime import date
from decimal import Decimal

from application.services.expense_reimbursement_write import (
    ReimbursementCommand,
    ReimbursementDeleteCommand,
    delete_reimbursement,
    save_reimbursement,
)
from application.services.transactional_write import WriteCode
from infrastructure.persistence.expense_reimbursement_write_adapter import (
    GestionDbReimbursementWriteAdapter,
)


class SqliteGestionDbCompat:
    def __init__(self, *, fail_on_assign=False):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.echec = 0
        self.isNetwork = False
        self.commit_count = 0
        self.fail_on_assign = fail_on_assign
        self._assign_count = 0
        self._create_fixture()

    def _create_fixture(self):
        self.cursor.executescript(
            """
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY
            );
            CREATE TABLE remboursements (
                IDremboursement INTEGER PRIMARY KEY AUTOINCREMENT,
                IDpersonne INTEGER,
                date TEXT,
                montant REAL,
                listeIDdeplacement TEXT
            );
            CREATE TABLE deplacements (
                IDdeplacement INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                IDremboursement INTEGER
            );
            INSERT INTO personnes VALUES (1);
            INSERT INTO deplacements VALUES (7, 1, 0);
            INSERT INTO deplacements VALUES (8, 1, NULL);
            INSERT INTO deplacements VALUES (9, 1, 0);
            """
        )
        self.connexion.commit()

    def ReqInsert(self, table, values, commit=True):
        columns = [name for name, _value in values]
        payload = [value for _name, value in values]
        placeholders = ", ".join("?" for _value in payload)
        self.cursor.execute(
            "INSERT INTO %s (%s) VALUES (%s)"
            % (table, ", ".join(columns), placeholders),
            payload,
        )
        inserted = int(self.cursor.lastrowid)
        if commit:
            self.Commit()
        return inserted

    def Commit(self):
        self.commit_count += 1
        self.connexion.commit()


def _command(**changes):
    values = dict(
        person_id=1,
        payment_date=date(2026, 9, 5),
        amount=Decimal("52.80"),
        checked_trip_ids=(7, 8),
        unchecked_trip_ids=(),
        reimbursement_id=None,
        confirm_zero_amount=False,
    )
    values.update(changes)
    return ReimbursementCommand(**values)


def test_create_reimbursement_and_trip_links_commit_together():
    db = SqliteGestionDbCompat()
    port = GestionDbReimbursementWriteAdapter(db)

    result = save_reimbursement(port, command=_command())

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert result.target_id == 1
    assert result.value.trip_ids == (7, 8)
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT IDpersonne, date, montant, listeIDdeplacement "
        "FROM remboursements WHERE IDremboursement=1"
    ).fetchone() == (1, "2026-09-05", 52.8, "7-8")
    assert db.connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 1), (8, 1), (9, 0)]


def test_modify_reimbursement_reconciles_unchecked_and_new_trip():
    db = SqliteGestionDbCompat()
    db.connexion.execute(
        "INSERT INTO remboursements VALUES (3, 1, '2026-09-01', 10.0, '7')"
    )
    db.connexion.execute(
        "UPDATE deplacements SET IDremboursement=3 WHERE IDdeplacement=7"
    )
    db.connexion.commit()
    port = GestionDbReimbursementWriteAdapter(db)

    result = save_reimbursement(
        port,
        command=_command(
            reimbursement_id=3,
            checked_trip_ids=(8,),
            unchecked_trip_ids=(7,),
            amount=Decimal("20.00"),
        ),
    )

    assert result.ok is True
    assert result.target_id == 3
    assert result.value.trip_ids == (8,)
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT montant, listeIDdeplacement FROM remboursements WHERE IDremboursement=3"
    ).fetchone() == (20.0, "8")
    assert db.connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 0), (8, 3), (9, 0)]


def test_concurrent_reassignment_is_never_stolen_and_rolls_back_parent():
    db = SqliteGestionDbCompat()
    db.connexion.execute(
        "UPDATE deplacements SET IDremboursement=99 WHERE IDdeplacement=7"
    )
    db.connexion.commit()
    port = GestionDbReimbursementWriteAdapter(db)

    result = save_reimbursement(
        port,
        command=_command(checked_trip_ids=(7,), unchecked_trip_ids=()),
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert "autre remboursement" in result.message
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM remboursements"
    ).fetchone()[0] == 0
    assert db.connexion.execute(
        "SELECT IDremboursement FROM deplacements WHERE IDdeplacement=7"
    ).fetchone() == (99,)


def test_missing_trip_rolls_back_new_reimbursement():
    db = SqliteGestionDbCompat()
    port = GestionDbReimbursementWriteAdapter(db)

    result = save_reimbursement(
        port,
        command=_command(checked_trip_ids=(777,), unchecked_trip_ids=()),
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert "n'existe plus" in result.message
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM remboursements"
    ).fetchone()[0] == 0


def test_invalid_zero_amount_never_reaches_database_without_confirmation():
    db = SqliteGestionDbCompat()
    port = GestionDbReimbursementWriteAdapter(db)

    result = save_reimbursement(
        port,
        command=_command(amount=Decimal("0"), confirm_zero_amount=False),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM remboursements"
    ).fetchone()[0] == 0


def test_zero_amount_is_allowed_only_when_explicitly_confirmed():
    db = SqliteGestionDbCompat()
    port = GestionDbReimbursementWriteAdapter(db)

    result = save_reimbursement(
        port,
        command=_command(
            amount=Decimal("0"),
            confirm_zero_amount=True,
            checked_trip_ids=(),
        ),
    )

    assert result.ok is True
    assert result.value.amount == Decimal("0.0")
    assert db.commit_count == 1


class FailingAssignAdapter(GestionDbReimbursementWriteAdapter):
    def __init__(self, db):
        super().__init__(db)
        self.calls = 0

    def assign_trip(self, trip_id, reimbursement_id):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("panne injectée pendant le rattachement")
        return super().assign_trip(trip_id, reimbursement_id)


def test_sql_failure_during_child_assignment_rolls_back_parent_and_children():
    db = SqliteGestionDbCompat()
    port = FailingAssignAdapter(db)

    result = save_reimbursement(port, command=_command())

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert "panne injectée" in result.message
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM remboursements"
    ).fetchone()[0] == 0
    assert db.connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 0), (8, None), (9, 0)]


class BrokenReadbackAdapter(GestionDbReimbursementWriteAdapter):
    def read_reimbursement(self, reimbursement_id):
        raise RuntimeError("readback cassé")


def test_readback_failure_is_distinguished_after_commit():
    db = SqliteGestionDbCompat()
    port = BrokenReadbackAdapter(db)

    result = save_reimbursement(port, command=_command())

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert result.target_id == 1
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM remboursements"
    ).fetchone()[0] == 1


def test_checked_and_unchecked_sets_cannot_overlap():
    db = SqliteGestionDbCompat()
    port = GestionDbReimbursementWriteAdapter(db)

    result = save_reimbursement(
        port,
        command=_command(checked_trip_ids=(7,), unchecked_trip_ids=(7,)),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "simultanément" in result.message
    assert db.connexion.execute(
        "SELECT COUNT(*) FROM remboursements"
    ).fetchone()[0] == 0


def test_common_frais_boundary_has_no_wx_or_qt_import():
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "application"
        / "services"
        / "expense_reimbursement_write.py"
    ).read_text(encoding="utf-8")
    assert "import wx" not in source
    assert "from wx" not in source
    assert "PySide6" not in source


def _seed_reimbursement(db, *, reimbursement_id=3, trip_ids=(7, 8)):
    db.connexion.execute(
        "INSERT INTO remboursements VALUES (?, 1, '2026-09-01', 20.0, ?)",
        (reimbursement_id, "-".join(str(value) for value in trip_ids)),
    )
    for trip_id in trip_ids:
        db.connexion.execute(
            "UPDATE deplacements SET IDremboursement=? WHERE IDdeplacement=?",
            (reimbursement_id, trip_id),
        )
    db.connexion.commit()


def test_delete_reimbursement_requires_explicit_confirmation_before_database_access():
    db = SqliteGestionDbCompat()
    _seed_reimbursement(db)
    port = GestionDbReimbursementWriteAdapter(db)

    result = delete_reimbursement(
        port,
        command=ReimbursementDeleteCommand(
            person_id=1,
            reimbursement_id=3,
            confirmed=False,
            confirm_attached_trips=True,
        ),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert result.committed is False
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT IDremboursement FROM remboursements WHERE IDremboursement=3"
    ).fetchone() == (3,)


def test_delete_reimbursement_with_attached_trips_requires_specific_confirmation():
    db = SqliteGestionDbCompat()
    _seed_reimbursement(db)
    port = GestionDbReimbursementWriteAdapter(db)

    result = delete_reimbursement(
        port,
        command=ReimbursementDeleteCommand(
            person_id=1,
            reimbursement_id=3,
            confirmed=True,
            confirm_attached_trips=False,
        ),
    )

    assert result.code == WriteCode.VALIDATION_ERROR
    assert "déplacement(s) rattaché(s)" in result.message
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 3), (8, 3), (9, 0)]


def test_delete_reimbursement_detaches_children_and_deletes_parent_atomically():
    db = SqliteGestionDbCompat()
    _seed_reimbursement(db)
    port = GestionDbReimbursementWriteAdapter(db)

    result = delete_reimbursement(
        port,
        command=ReimbursementDeleteCommand(
            person_id=1,
            reimbursement_id=3,
            confirmed=True,
            confirm_attached_trips=True,
        ),
    )

    assert result.ok is True
    assert result.code == WriteCode.OK
    assert result.committed is True
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT IDremboursement FROM remboursements WHERE IDremboursement=3"
    ).fetchone() is None
    assert db.connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 0), (8, 0), (9, 0)]


class FailingDeleteAdapter(GestionDbReimbursementWriteAdapter):
    def delete_reimbursement(self, reimbursement_id, person_id):
        raise RuntimeError("panne injectée pendant DELETE parent")


def test_delete_failure_rolls_back_child_detachments_and_parent():
    db = SqliteGestionDbCompat()
    _seed_reimbursement(db)
    port = FailingDeleteAdapter(db)

    result = delete_reimbursement(
        port,
        command=ReimbursementDeleteCommand(
            person_id=1,
            reimbursement_id=3,
            confirmed=True,
            confirm_attached_trips=True,
        ),
    )

    assert result.code == WriteCode.DATABASE_ERROR
    assert result.committed is False
    assert db.commit_count == 0
    assert db.connexion.execute(
        "SELECT IDremboursement FROM remboursements WHERE IDremboursement=3"
    ).fetchone() == (3,)
    assert db.connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 3), (8, 3), (9, 0)]


class UnexpectedDeleteRowcountAdapter(GestionDbReimbursementWriteAdapter):
    def delete_reimbursement(self, reimbursement_id, person_id):
        super().delete_reimbursement(reimbursement_id, person_id)
        return 2


def test_delete_unexpected_parent_rowcount_rolls_back_everything():
    db = SqliteGestionDbCompat()
    _seed_reimbursement(db)
    port = UnexpectedDeleteRowcountAdapter(db)

    result = delete_reimbursement(
        port,
        command=ReimbursementDeleteCommand(
            person_id=1,
            reimbursement_id=3,
            confirmed=True,
            confirm_attached_trips=True,
        ),
    )

    assert result.code == WriteCode.UNEXPECTED_ROWCOUNT
    assert result.committed is False
    assert db.connexion.execute(
        "SELECT IDremboursement FROM remboursements WHERE IDremboursement=3"
    ).fetchone() == (3,)
    assert db.connexion.execute(
        "SELECT IDdeplacement, IDremboursement FROM deplacements ORDER BY IDdeplacement"
    ).fetchall() == [(7, 3), (8, 3), (9, 0)]


class BrokenDeleteReadbackAdapter(GestionDbReimbursementWriteAdapter):
    def has_trip_assignment(self, reimbursement_id):
        raise RuntimeError("readback suppression cassé")


def test_delete_readback_failure_is_distinguished_after_commit():
    db = SqliteGestionDbCompat()
    _seed_reimbursement(db)
    port = BrokenDeleteReadbackAdapter(db)

    result = delete_reimbursement(
        port,
        command=ReimbursementDeleteCommand(
            person_id=1,
            reimbursement_id=3,
            confirmed=True,
            confirm_attached_trips=True,
        ),
    )

    assert result.code == WriteCode.READBACK_ERROR
    assert result.ok is False
    assert result.committed is True
    assert db.commit_count == 1
    assert db.connexion.execute(
        "SELECT IDremboursement FROM remboursements WHERE IDremboursement=3"
    ).fetchone() is None
