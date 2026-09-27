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
SCHEMA = ROOT / "infrastructure" / "persistence" / "sql" / "mysql" / "termination_v1.sql"

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


def _apply_schema() -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS tw_contract_termination")
        cur.execute(SCHEMA.read_text(encoding="utf-8").strip().rstrip(";"))
        conn.commit()
    finally:
        conn.close()


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
    conn = termination_mysql_server()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM tw_contract_termination")
        conn.commit()
    finally:
        conn.close()
    return termination_mysql_server
