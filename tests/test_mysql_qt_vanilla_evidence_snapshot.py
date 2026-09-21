from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


if os.getenv("TEAMWORKS_MYSQL_INTEGRATION") != "1":
    pytest.skip("Recette MySQL désactivée", allow_module_level=True)

mysql = pytest.importorskip("mysql.connector")

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "collect_qt_vanilla_mysql_evidence.py"
DATABASE = "teamworks_evidence_ci_qt_vanilla_recette"
SHA = "1" * 40


def _server_connection(database=None):
    kwargs = dict(
        host=os.getenv("TEAMWORKS_MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("TEAMWORKS_MYSQL_PORT", "3306")),
        user=os.getenv("TEAMWORKS_MYSQL_USER", "root"),
        password=os.getenv("TEAMWORKS_MYSQL_PASSWORD", ""),
        use_pure=True,
        ssl_disabled=True,
    )
    if database:
        kwargs["database"] = database
    return mysql.connect(**kwargs)


def _create_fixture():
    connection = _server_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE}")
        cursor.execute(
            f"CREATE DATABASE {DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    finally:
        cursor.close()
        connection.close()

    connection = _server_connection(DATABASE)
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE personnes (
                IDpersonne INTEGER PRIMARY KEY,
                nom VARCHAR(100)
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE contrats (
                IDcontrat INTEGER PRIMARY KEY,
                IDpersonne INTEGER,
                date_debut DATE,
                INDEX idx_contrats_personne (IDpersonne)
            ) ENGINE=InnoDB
            """
        )
        cursor.execute("INSERT INTO personnes VALUES (1, 'Personne de recette')")
        cursor.execute("INSERT INTO contrats VALUES (10, 1, '2026-09-01')")
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def _drop_fixture():
    connection = _server_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE}")
    finally:
        cursor.close()
        connection.close()


def test_snapshot_and_compare_run_against_real_mysql(tmp_path):
    _create_fixture()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + str(ROOT / "teamworks")
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    compare = tmp_path / "compare.json"

    try:
        for label, output in (("before", before), ("after", after)):
            process = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "snapshot",
                    "--database",
                    DATABASE,
                    "--sha",
                    SHA,
                    "--label",
                    label,
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                timeout=60,
            )
            assert process.returncode == 0, process.stdout + "\n" + process.stderr

        process = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "compare",
                "--before",
                str(before),
                "--after",
                str(after),
                "--output",
                str(compare),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert process.returncode == 0, process.stdout + "\n" + process.stderr

        snapshot = json.loads(before.read_text(encoding="utf-8"))
        assert snapshot["rc_sha"] == SHA
        assert snapshot["database"] == DATABASE
        assert snapshot["counts"]["personnes"] == 1
        assert snapshot["counts"]["contrats"] == 1
        assert snapshot["mysql_version"]
        assert snapshot["schema"]["tables_hash"]
        assert snapshot["schema"]["columns_hash"]
        assert snapshot["schema"]["indexes_hash"]

        report = json.loads(compare.read_text(encoding="utf-8"))
        assert report["automatic_schema_gate"] is True
        assert report["count_deltas"]["personnes"] == 0
        assert report["count_deltas"]["contrats"] == 0
    finally:
        _drop_fixture()
