"""Tests de connect_mysql() avec un faux module mysql.connector injecté.

connect_mysql() importe mysql-connector-python à l'appel (voir
legacy_mysql_inventory_adapter.py). En injectant un faux module dans
sys.modules pour la durée du test, on vérifie le comportement réel de
connect_mysql() (kwargs transmis, fermeture en cas d'échec de négociation)
sans dépendre du paquet mysql-connector-python installé, ni d'un serveur
MySQL réel.
"""

import sys
import types

import pytest

from infrastructure.persistence.legacy_mysql_inventory_adapter import (
    MySqlReadOnlyGuaranteeError,
    connect_mysql,
)


class _FakeCursor:
    def __init__(self, *, version, grants=()):
        self._version = version
        self._grants = grants
        self._last_sql = None

    def execute(self, sql, params=()):
        self._last_sql = sql

    def fetchone(self):
        return (self._version,)

    def fetchall(self):
        return [(g,) for g in self._grants]


class _FakeMySqlConnection:
    def __init__(self, *, version, grants=(), **connect_kwargs):
        self.connect_kwargs = connect_kwargs
        self._version = version
        self._grants = grants
        self.closed = False
        self.readonly_transaction_calls: list[bool] = []

    def cursor(self):
        return _FakeCursor(version=self._version, grants=self._grants)

    def start_transaction(self, *, readonly: bool) -> None:
        self.readonly_transaction_calls.append(readonly)

    def close(self) -> None:
        self.closed = True


def _install_fake_mysql_connector(monkeypatch, *, version, grants=()):
    created: list[_FakeMySqlConnection] = []

    def fake_connect(**kwargs):
        connection = _FakeMySqlConnection(version=version, grants=grants, **kwargs)
        created.append(connection)
        return connection

    fake_connector_module = types.SimpleNamespace(connect=fake_connect)
    fake_mysql_package = types.ModuleType("mysql")
    fake_mysql_package.connector = fake_connector_module

    monkeypatch.setitem(sys.modules, "mysql", fake_mysql_package)
    monkeypatch.setitem(sys.modules, "mysql.connector", fake_connector_module)
    return created


def test_connect_mysql_passes_expected_arguments(monkeypatch):
    created = _install_fake_mysql_connector(monkeypatch, version="8.0.39")

    connection = connect_mysql(
        host="db.example.org",
        port=3306,
        user="lecture",
        password="secret",
        database="teamworks",
    )

    assert connection is created[0]
    assert created[0].connect_kwargs["host"] == "db.example.org"
    assert created[0].connect_kwargs["port"] == 3306
    assert created[0].connect_kwargs["user"] == "lecture"
    assert created[0].connect_kwargs["password"] == "secret"
    assert created[0].connect_kwargs["database"] == "teamworks"


def test_connect_mysql_uses_readonly_transaction_for_modern_server(monkeypatch):
    created = _install_fake_mysql_connector(monkeypatch, version="8.0.39")

    connection = connect_mysql(
        host="h", port=3306, user="u", password="p", database="d"
    )

    assert connection.readonly_transaction_calls == [True]
    assert created[0].closed is False


def test_connect_mysql_accepts_old_server_with_select_only_account(monkeypatch):
    _install_fake_mysql_connector(
        monkeypatch,
        version="5.5.62-log",
        grants=["GRANT SELECT ON `teamworks`.* TO 'lecture'@'%'"],
    )

    connection = connect_mysql(
        host="h", port=3306, user="lecture", password="p", database="d"
    )

    assert connection.readonly_transaction_calls == []
    assert connection.closed is False


def test_connect_mysql_closes_and_raises_for_old_server_with_write_account(monkeypatch):
    created = _install_fake_mysql_connector(
        monkeypatch,
        version="5.5.62-log",
        grants=["GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%'"],
    )

    with pytest.raises(MySqlReadOnlyGuaranteeError, match="SELECT-only"):
        connect_mysql(host="h", port=3306, user="admin", password="p", database="d")

    assert created[0].closed is True
