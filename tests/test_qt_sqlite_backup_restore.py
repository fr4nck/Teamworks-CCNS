"""Sauvegardes SQLite uniques et restauration isolée, jamais sur la base active."""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from infrastructure.persistence.sqlite_backup import (
    backup_open_sqlite,
    inspect_sqlite_copy,
    restore_sqlite_backup,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def base(tmp_path):
    path = tmp_path / "Recette_TDATA.dat"
    with sqlite3.connect(path) as c:
        c.execute("CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, nom TEXT)")
        c.execute("CREATE TABLE contrats (IDcontrat INTEGER PRIMARY KEY, IDpersonne INTEGER, date_debut TEXT)")
        c.executemany("INSERT INTO personnes (nom) VALUES (?)", [("Martin",), ("Durand",)])
        c.execute("INSERT INTO contrats (IDpersonne, date_debut) VALUES (1, '2026-01-05')")
    return path


def test_two_backups_at_the_same_instant_get_distinct_verified_files(base):
    instant = datetime(2026, 10, 29, 9, 0, 0, 0)
    connection = sqlite3.connect(base)
    try:
        first = backup_open_sqlite(connection, str(base), "test", now=instant)
        connection.execute("INSERT INTO personnes (nom) VALUES ('Petit')")
        connection.commit()
        second = backup_open_sqlite(connection, str(base), "test", now=instant)
    finally:
        connection.close()
    assert first != second
    assert Path(second).name.endswith("-2.bak")
    with sqlite3.connect(first) as c:
        assert inspect_sqlite_copy(c).row_counts == {"contrats": 1, "personnes": 2}
    with sqlite3.connect(second) as c:
        assert inspect_sqlite_copy(c).row_counts == {"contrats": 1, "personnes": 3}


def test_restore_goes_to_a_new_isolated_file_with_identical_content(base, tmp_path):
    connection = sqlite3.connect(base)
    try:
        backup = backup_open_sqlite(connection, str(base), "test")
        expected = inspect_sqlite_copy(connection)
    finally:
        connection.close()
    with sqlite3.connect(base) as c:
        c.execute("DELETE FROM contrats")
    active_digest = _digest(base)
    backup_digest = _digest(Path(backup))

    isolated = tmp_path / "restauration" / "Restaure_TDATA.dat"
    isolated.parent.mkdir()
    restored = restore_sqlite_backup(backup, str(isolated), active_paths=(str(base),))

    assert restored == expected and restored.integrity == "ok"
    with sqlite3.connect(isolated) as c:
        assert c.execute("SELECT IDpersonne, date_debut FROM contrats").fetchall() == [(1, "2026-01-05")]
    assert _digest(base) == active_digest
    assert _digest(Path(backup)) == backup_digest


def test_restore_refuses_active_base_existing_file_and_backup_itself(base, tmp_path):
    connection = sqlite3.connect(base)
    try:
        backup = backup_open_sqlite(connection, str(base), "test")
    finally:
        connection.close()
    active_digest = _digest(base)
    with pytest.raises(ValueError, match="base active"):
        restore_sqlite_backup(backup, str(base), active_paths=(str(base),))
    occupied = tmp_path / "occupe.dat"
    occupied.write_bytes(b"x")
    with pytest.raises(ValueError, match="existe déjà"):
        restore_sqlite_backup(backup, str(occupied), active_paths=(str(base),))
    with pytest.raises(ValueError, match="sauvegarde elle-même"):
        restore_sqlite_backup(backup, backup, active_paths=(str(base),))
    assert _digest(base) == active_digest
    assert occupied.read_bytes() == b"x"


def test_restore_rejects_a_corrupted_backup_and_leaves_no_usable_copy(base, tmp_path):
    damaged = tmp_path / "abime.bak"
    raw = bytearray(base.read_bytes())
    raw[100:4096] = b"\xff" * (4096 - 100)
    damaged.write_bytes(bytes(raw))
    target = tmp_path / "restaure.dat"
    with pytest.raises((RuntimeError, sqlite3.DatabaseError)):
        restore_sqlite_backup(str(damaged), str(target), active_paths=(str(base),))
    assert not target.exists()
