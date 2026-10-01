import json
import sqlite3
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("tools/inventory_legacy_database.py")


def run_cli(*args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _clean_sqlite(tmp_path) -> Path:
    path = tmp_path / "legacy.sqlite"
    connection = sqlite3.connect(str(path))
    connection.executescript(
        """
        CREATE TABLE personnes (IDpersonne INTEGER PRIMARY KEY, nom VARCHAR(100));
        CREATE TABLE deplacements (
            IDdeplacement INTEGER PRIMARY KEY,
            IDpersonne INTEGER,
            date DATE,
            objet VARCHAR(100),
            cp_depart VARCHAR(5),
            cp_arrivee VARCHAR(5),
            distance FLOAT,
            aller_retour VARCHAR(5),
            tarif_km FLOAT,
            IDremboursement INTEGER
        );
        CREATE TABLE remboursements (
            IDremboursement INTEGER PRIMARY KEY,
            IDpersonne INTEGER,
            date DATE,
            montant FLOAT,
            listeIDdeplacement VARCHAR(300)
        );
        INSERT INTO personnes VALUES (12, 'Dupont');
        INSERT INTO deplacements VALUES
            (7, 12, '2026-09-10', 'Réunion', '03510', '35000', 20.0, '0', 0.5, 3);
        INSERT INTO remboursements VALUES (3, 12, '2026-09-30', 10.0, '7');
        """
    )
    connection.commit()
    connection.close()
    return path


def test_missing_sqlite_file_returns_non_zero_exit_code(tmp_path):
    missing = tmp_path / "absent.sqlite"

    result = run_cli("--sqlite", str(missing))

    assert result.returncode == 1
    assert "ERREUR" in result.stderr


def test_missing_mysql_password_env_returns_non_zero_exit_code():
    result = run_cli(
        "--mysql-host", "db.example.org",
        "--mysql-user", "lecture",
        "--mysql-database", "noethys",
        "--mysql-password-env", "THIS_ENV_VAR_DOES_NOT_EXIST_12345",
    )

    assert result.returncode == 1
    assert "ERREUR" in result.stderr


def test_mysql_without_required_options_is_a_usage_error():
    result = run_cli("--mysql-host", "db.example.org")

    assert result.returncode == 2


def test_clean_sqlite_produces_json_and_markdown(tmp_path):
    db_path = _clean_sqlite(tmp_path)
    json_path = tmp_path / "out.json"
    markdown_path = tmp_path / "out.md"

    result = run_cli(
        "--sqlite", str(db_path),
        "--json", str(json_path),
        "--markdown", str(markdown_path),
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["decision"] == "READY_FOR_MIGRATION_ANALYSIS"
    assert summary["blocking_findings"] == 0

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["decision"] == "READY_FOR_MIGRATION_ANALYSIS"
    assert payload["expense_pilot"]["trip_count"] == 1

    markdown_text = markdown_path.read_text(encoding="utf-8")
    assert "Base inspectée" in markdown_text
    assert "READY_FOR_MIGRATION_ANALYSIS" in markdown_text


def test_never_writes_to_the_source_database(tmp_path):
    db_path = _clean_sqlite(tmp_path)
    before = db_path.read_bytes()

    run_cli("--sqlite", str(db_path))

    assert db_path.read_bytes() == before


def test_no_frais_flag_skips_expense_pilot_analysis(tmp_path):
    db_path = _clean_sqlite(tmp_path)
    json_path = tmp_path / "out.json"

    result = run_cli("--sqlite", str(db_path), "--json", str(json_path), "--no-frais")

    assert result.returncode == 0, result.stderr
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["expense_pilot"] is None
