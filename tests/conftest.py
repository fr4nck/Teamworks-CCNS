"""Infrastructure de test commune.

Sous GitHub Actions, la suite pytest démarre un MariaDB épinglé comme service
Docker et exporte DPAE_MYSQL_* avant la collecte des modules d'intégration.
En local, aucun conteneur n'est lancé implicitement : les variables existantes
continuent de permettre une base de recette choisie par le développeur.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

_CONTAINER = "teamworks-dpae-mariadb-ci"
_IMAGE = "mariadb:10.11.14"
_CI_ENV = {
    "DPAE_MYSQL_HOST": "127.0.0.1",
    "DPAE_MYSQL_PORT": "33306",
    "DPAE_MYSQL_USER": "teamworks",
    "DPAE_MYSQL_PASSWORD": "teamworks-ci-only",
    "DPAE_MYSQL_DATABASE": "teamworks_dpae_ci",
}
_started = False


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def _wait_ready(timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        probe = _run(
            "docker", "exec", _CONTAINER,
            "mariadb-admin", "ping", "-h", "127.0.0.1",
            "-uteamworks", "-pteamworks-ci-only", "--silent",
            check=False,
        )
        if probe.returncode == 0:
            return
        last = (probe.stderr or probe.stdout).strip()
        time.sleep(1)
    logs = _run("docker", "logs", _CONTAINER, check=False)
    raise RuntimeError(f"MariaDB DPAE CI non prêt après {timeout}s: {last}\n{logs.stdout}\n{logs.stderr}")


def _apply_schema() -> None:
    import mysql.connector

    conn = mysql.connector.connect(
        host=os.environ["DPAE_MYSQL_HOST"],
        port=int(os.environ["DPAE_MYSQL_PORT"]),
        user=os.environ["DPAE_MYSQL_USER"],
        password=os.environ["DPAE_MYSQL_PASSWORD"],
        database=os.environ["DPAE_MYSQL_DATABASE"],
        autocommit=True,
    )
    try:
        cur = conn.cursor()
        sql = Path("infrastructure/persistence/sql/mysql/dpae_v1.sql").read_text(encoding="utf-8")
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                cur.execute(statement)
        cur.close()
    finally:
        conn.close()


def pytest_configure(config) -> None:
    global _started
    if os.getenv("GITHUB_ACTIONS") != "true":
        return
    # Une CI DPAE ne doit jamais se transformer silencieusement en tests skip.
    for key, value in _CI_ENV.items():
        os.environ[key] = value
    _run("docker", "rm", "-f", _CONTAINER, check=False)
    _run(
        "docker", "run", "-d", "--name", _CONTAINER,
        "-p", "33306:3306",
        "-e", "MARIADB_ROOT_PASSWORD=root-ci-only",
        "-e", "MARIADB_DATABASE=teamworks_dpae_ci",
        "-e", "MARIADB_USER=teamworks",
        "-e", "MARIADB_PASSWORD=teamworks-ci-only",
        "--health-cmd=healthcheck.sh --connect --innodb_initialized",
        "--health-interval=2s", "--health-timeout=3s", "--health-retries=30",
        _IMAGE,
    )
    _started = True
    _wait_ready()
    _apply_schema()


def pytest_sessionfinish(session, exitstatus) -> None:
    if not _started:
        return
    # Laisser les logs dans la sortie Actions en cas d'échec avant suppression.
    if exitstatus != 0:
        logs = _run("docker", "logs", _CONTAINER, check=False)
        print("\n===== MariaDB DPAE CI logs =====\n" + logs.stdout + logs.stderr)
    _run("docker", "rm", "-f", _CONTAINER, check=False)
