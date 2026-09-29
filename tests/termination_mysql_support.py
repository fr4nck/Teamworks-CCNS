"""Base MariaDB/MySQL réelle pour les tests de persistance des sorties salarié.

Configuration par variables d'environnement TERMINATION_MYSQL_HOST, _PORT,
_USER, _PASSWORD, _DATABASE. Sur GitHub Actions, un conteneur MariaDB dédié
est démarré sur un port propre (aucun partage avec d'autres suites) et
l'absence de base fait échouer les tests au lieu de les ignorer : une preuve de
concurrence ne doit jamais disparaître silencieusement de la CI.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "infrastructure" / "persistence" / "sql" / "mysql"
SCHEMA = SQL_DIR / "termination_v1.sql"
SCHEMAS = (
    SQL_DIR / "termination_v1.sql",
    SQL_DIR / "termination_v2.sql",
    SQL_DIR / "termination_v2_guards.sql",
)
# Ordre de suppression compatible avec les clés étrangères.
TABLES = ("tw_termination_command", "tw_termination_transmission_snapshot", "tw_contract_termination")

_CONTAINER = "teamworks-termination-mariadb-ci"
_IMAGE = "mariadb:10.11.14"
_CI_ENV = {
    "TERMINATION_MYSQL_HOST": "127.0.0.1",
    "TERMINATION_MYSQL_PORT": "33307",
    "TERMINATION_MYSQL_USER": "teamworks",
    "TERMINATION_MYSQL_PASSWORD": "teamworks-ci-only",
    "TERMINATION_MYSQL_DATABASE": "teamworks_termination_ci",
}


def _in_ci() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def connect(**overrides):
    import mysql.connector

    options = dict(
        host=os.environ["TERMINATION_MYSQL_HOST"],
        port=int(os.environ.get("TERMINATION_MYSQL_PORT", "3306")),
        user=os.environ["TERMINATION_MYSQL_USER"],
        password=os.environ.get("TERMINATION_MYSQL_PASSWORD", ""),
        database=os.environ["TERMINATION_MYSQL_DATABASE"],
        use_pure=True,
        autocommit=False,
    )
    options.update(overrides)
    return mysql.connector.connect(**options)


def _start_ci_container() -> None:
    for key, value in _CI_ENV.items():
        os.environ[key] = value
    _run("docker", "rm", "-f", _CONTAINER, check=False)
    _run(
        "docker", "run", "-d", "--name", _CONTAINER, "-p", "33307:3306",
        "-e", "MARIADB_ROOT_PASSWORD=root-ci-only",
        "-e", "MARIADB_DATABASE=" + _CI_ENV["TERMINATION_MYSQL_DATABASE"],
        "-e", "MARIADB_USER=teamworks",
        "-e", "MARIADB_PASSWORD=" + _CI_ENV["TERMINATION_MYSQL_PASSWORD"],
        _IMAGE,
    )
    deadline = time.monotonic() + 90
    last_error = None
    while time.monotonic() < deadline:
        try:
            connect().close()
            return
        except Exception as exc:  # serveur en cours de démarrage
            last_error = exc
            time.sleep(1)
    logs = _run("docker", "logs", _CONTAINER, check=False)
    raise RuntimeError(
        "MariaDB termination CI non prête: %r\n%s%s" % (last_error, logs.stdout, logs.stderr)
    )


def _configured() -> bool:
    return all(
        os.getenv(key)
        for key in ("TERMINATION_MYSQL_HOST", "TERMINATION_MYSQL_USER", "TERMINATION_MYSQL_DATABASE")
    )


def schema_statements(path: Path) -> list[str]:
    """Instructions d'un fichier SQL : commentaires retirés, séparateur ';'."""
    text = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    )
    return [statement.strip() for statement in text.split(";") if statement.strip()]


def reset_schema(connect_fn=None, schemas=SCHEMAS) -> None:
    """Recrée les tables : les tables en ajout seul refusent DELETE (déclencheurs)."""
    conn = (connect_fn or connect)()
    try:
        cur = conn.cursor()
        for table in TABLES:
            cur.execute("DROP TABLE IF EXISTS " + table)
        for path in schemas:
            for statement in schema_statements(path):
                cur.execute(statement)
        conn.commit()
    finally:
        conn.close()


def _apply_schema() -> None:
    reset_schema()


@pytest.fixture(scope="session")
def termination_mysql_server():
    started = False
    if _in_ci() and not _configured():
        try:
            _start_ci_container()
            started = True
        except Exception as exc:
            pytest.fail("Base MariaDB requise en CI pour SORTIE-002: %s" % exc)
    if not _configured():
        pytest.skip("base MySQL/MariaDB termination non configurée (TERMINATION_MYSQL_*)")
    try:
        import mysql.connector  # noqa: F401
    except ImportError:
        if _in_ci():
            pytest.fail("mysql-connector-python requis en CI pour SORTIE-002")
        pytest.skip("mysql-connector-python non installé")
    _apply_schema()
    try:
        yield connect
    finally:
        if started:
            _run("docker", "rm", "-f", _CONTAINER, check=False)


@pytest.fixture
def termination_db(termination_mysql_server):
    reset_schema(termination_mysql_server)
    return termination_mysql_server
