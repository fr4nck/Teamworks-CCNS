#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from pathlib import Path

from tools import diagnostic_installation


def _complete_package(root: Path) -> None:
    for relative_path in diagnostic_installation.REQUIRED_RESOURCES:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test")


def test_build_report_success(tmp_path: Path) -> None:
    root = tmp_path / "package"
    _complete_package(root)

    user_directory = tmp_path / "user"
    report, success = diagnostic_installation.build_report(root, user_directory)

    assert success is True
    assert "Résultat global: OK" in report
    assert "Base contrôlée: non demandée" in report
    assert str(user_directory) in report


def test_build_report_reports_missing_resources(tmp_path: Path) -> None:
    root = tmp_path / "empty-package"
    root.mkdir()

    report, success = diagnostic_installation.build_report(root, tmp_path / "user")

    assert success is False
    assert "[ERREUR] Ressource" in report
    assert "Résultat global: ERREUR" in report


def test_database_preflight_reads_valid_database_without_modifying_it(tmp_path: Path) -> None:
    root = tmp_path / "package"
    _complete_package(root)
    database = tmp_path / "copie_test.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE personnes (id INTEGER PRIMARY KEY, nom TEXT)")
        connection.execute("INSERT INTO personnes (nom) VALUES ('Test')")
        connection.commit()

    # Une copie exploitable doit avoir son WAL consolidé dans le fichier principal.
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    before_bytes = database.read_bytes()
    before_entries = sorted(path.name for path in tmp_path.iterdir())
    report, success = diagnostic_installation.build_report(
        root,
        tmp_path / "user",
        database,
    )

    assert success is True
    assert "[OK] Base SQLite" in report
    assert "lecture seule OK, intégrité OK, 1 table(s)" in report
    assert database.read_bytes() == before_bytes
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(before_entries + ["user"])
    assert not Path(f"{database}-wal").exists()
    assert not Path(f"{database}-shm").exists()


def test_database_preflight_rejects_missing_or_invalid_file(tmp_path: Path) -> None:
    missing = diagnostic_installation.check_database(tmp_path / "absente.sqlite")
    assert missing.ok is False
    assert "fichier introuvable" in missing.detail

    invalid = tmp_path / "invalide.sqlite"
    invalid.write_text("ceci n'est pas une base SQLite", encoding="utf-8")
    result = diagnostic_installation.check_database(invalid)
    assert result.ok is False
    assert "lecture seule impossible" in result.detail


def test_main_rejects_report_path_aliasing_database(tmp_path: Path) -> None:
    database = tmp_path / "donnees.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

    before = database.read_bytes()
    result = diagnostic_installation.main(
        ["--database", str(database), "--output", str(database)]
    )

    assert result == 2
    assert database.read_bytes() == before
