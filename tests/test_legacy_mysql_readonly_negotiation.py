"""Tests de la stratégie de lecture seule MySQL selon la version serveur.

start_transaction(readonly=True) n'existe côté serveur qu'à partir de
MySQL 5.6.5. En dessous (MySQL 5.5 historique compris), la seule garantie
possible est un compte SQL strictement SELECT-only : ces tests vérifient
que negotiate_read_only_mode() choisit la bonne stratégie et échoue
explicitement quand elle ne peut rien garantir.

Aucun serveur MySQL réel n'est nécessaire : voir docs/68 pour le statut
de qualification réel (MySQL 5.5 NON QUALIFIÉ, cette suite ne teste que la
logique de décision).
"""

import pytest

from infrastructure.persistence.legacy_mysql_inventory_adapter import (
    MySqlReadOnlyGuaranteeError,
    ensure_select_only_account,
    negotiate_read_only_mode,
    parse_mysql_version,
    supports_readonly_transaction,
)


class _FakeCursor:
    def __init__(self, grants):
        self._grants = grants

    def execute(self, sql, params=()):
        pass

    def fetchall(self):
        return [(g,) for g in self._grants]


class _FailingCursor:
    def execute(self, sql, params=()):
        raise RuntimeError("connexion perdue")

    def fetchall(self):
        raise AssertionError("ne doit pas être atteint")


class _FakeConnection:
    def __init__(self, *, grants=()):
        self._grants = grants
        self.readonly_transaction_calls: list[bool] = []

    def start_transaction(self, *, readonly: bool) -> None:
        self.readonly_transaction_calls.append(readonly)

    def cursor(self):
        return _FakeCursor(self._grants)


class _FakeConnectionWithFailingGrants:
    def start_transaction(self, *, readonly: bool) -> None:
        raise AssertionError("ne doit pas être atteint sur un vieux serveur")

    def cursor(self):
        return _FailingCursor()


def test_parse_mysql_version_extracts_major_minor_patch():
    assert parse_mysql_version("8.0.39") == (8, 0, 39)
    assert parse_mysql_version("5.5.62-log") == (5, 5, 62)
    assert parse_mysql_version("5.6.5") == (5, 6, 5)


def test_parse_mysql_version_rejects_unreadable_string():
    with pytest.raises(MySqlReadOnlyGuaranteeError):
        parse_mysql_version("not-a-version")
    with pytest.raises(MySqlReadOnlyGuaranteeError):
        parse_mysql_version("")


def test_supports_readonly_transaction_boundary_is_5_6_5():
    assert supports_readonly_transaction((5, 6, 5)) is True
    assert supports_readonly_transaction((5, 6, 6)) is True
    assert supports_readonly_transaction((8, 0, 39)) is True
    assert supports_readonly_transaction((5, 6, 4)) is False
    assert supports_readonly_transaction((5, 5, 62)) is False


def test_ensure_select_only_account_accepts_select_and_usage():
    ensure_select_only_account(
        [
            "GRANT USAGE ON *.* TO 'lecture'@'%'",
            "GRANT SELECT ON `teamworks`.* TO 'lecture'@'%'",
        ]
    )  # ne doit pas lever


def test_ensure_select_only_account_rejects_write_privileges():
    with pytest.raises(MySqlReadOnlyGuaranteeError):
        ensure_select_only_account(["GRANT SELECT, INSERT ON `teamworks`.* TO 'x'@'%'"])


def test_ensure_select_only_account_rejects_all_privileges():
    with pytest.raises(MySqlReadOnlyGuaranteeError):
        ensure_select_only_account(["GRANT ALL PRIVILEGES ON *.* TO 'x'@'%'"])


def test_ensure_select_only_account_rejects_empty_grants():
    with pytest.raises(MySqlReadOnlyGuaranteeError):
        ensure_select_only_account([])


def test_ensure_select_only_account_rejects_unparsable_grant():
    with pytest.raises(MySqlReadOnlyGuaranteeError):
        ensure_select_only_account(["not a grant statement"])


def test_negotiate_uses_readonly_transaction_for_modern_server():
    connection = _FakeConnection()

    negotiate_read_only_mode(connection, version_string="8.0.39")

    assert connection.readonly_transaction_calls == [True]


def test_negotiate_checks_grants_for_server_older_than_5_6_5():
    connection = _FakeConnection(grants=["GRANT SELECT ON `teamworks`.* TO 'lecture'@'%'"])

    negotiate_read_only_mode(connection, version_string="5.5.62-log")

    assert connection.readonly_transaction_calls == []


def test_negotiate_fails_explicitly_for_old_server_with_write_grants():
    connection = _FakeConnection(grants=["GRANT ALL PRIVILEGES ON *.* TO 'x'@'%'"])

    with pytest.raises(MySqlReadOnlyGuaranteeError, match="SELECT-only"):
        negotiate_read_only_mode(connection, version_string="5.5.62-log")

    assert connection.readonly_transaction_calls == []


def test_negotiate_fails_explicitly_when_grants_cannot_be_read():
    connection = _FakeConnectionWithFailingGrants()

    with pytest.raises(MySqlReadOnlyGuaranteeError, match="SELECT-only"):
        negotiate_read_only_mode(connection, version_string="5.5.62-log")


def test_negotiate_fails_explicitly_for_unparsable_version():
    connection = _FakeConnection()

    with pytest.raises(MySqlReadOnlyGuaranteeError):
        negotiate_read_only_mode(connection, version_string="")

    assert connection.readonly_transaction_calls == []
