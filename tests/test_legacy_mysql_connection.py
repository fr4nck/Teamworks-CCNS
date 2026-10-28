"""Compatibility tests for headless MySQL connection creation."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.persistence.legacy_mysql_connection import open_legacy_mysql
from infrastructure.persistence.legacy_network_target import parse_legacy_network_target


TARGET = parse_legacy_network_target(
    "3307;rh.example;staff;#64#c2VjcmV0[RESEAU]ASSOCIATION_TDATA"
)
SECRET = "secret"


def test_connector_driver_keeps_legacy_options_and_no_implicit_sql_or_commit():
    calls = []
    connection = SimpleNamespace()

    class Driver:
        __version__ = "9.5.0"

        @staticmethod
        def connect(**kwargs):
            calls.append(("connect", kwargs))
            return connection

    def decode(value):
        calls.append(("decode", value))
        return SECRET

    def options(host, user, password, port, certs):
        calls.append(("options", host, user, password, port, certs))
        return {
            "host": host, "user": user, "passwd": password,
            "port": port, "use_pure": True, "ssl_disabled": not bool(certs),
        }

    result, database = open_legacy_mysql(
        TARGET, driver="mysql.connector", decode_password=decode,
        certificates={}, mysql_connector=Driver,
        connector_options=options,
        connector_diagnostic=lambda *_: pytest.fail("No error expected"),
    )
    assert result is connection
    assert database == "association_tdata"
    assert calls == [
        ("decode", "#64#c2VjcmV0"),
        ("options", "rh.example", "staff", SECRET, 3307, {}),
        ("connect", {"host": "rh.example", "user": "staff", "passwd": SECRET,
                     "port": 3307, "use_pure": True, "ssl_disabled": True}),
    ]


def test_connector_driver_preserves_certificate_mapping():
    seen = []
    certs = {"ca": "ca.pem", "key": "key.pem", "cert": "cert.pem"}
    driver = SimpleNamespace(connect=lambda **kw: seen.append(kw) or object())
    out, db = open_legacy_mysql(
        TARGET, driver="mysql.connector", decode_password=lambda _: SECRET,
        certificates=certs, mysql_connector=driver,
        connector_options=lambda h, u, p, port, c: {
            "host": h, "user": u, "passwd": p, "port": port, "ssl_ca": c["ca"]
        },
        connector_diagnostic=lambda *_: "",
    )
    assert out is not None
    assert db == "association_tdata"
    assert seen[0]["ssl_ca"] == "ca.pem"


def test_connector_error_uses_existing_diagnostic_and_keeps_cause():
    class DriverError(RuntimeError):
        pass

    class Driver:
        __version__ = "9.5.0"

        @staticmethod
        def connect(**_kwargs):
            raise DriverError("Access denied")

    seen = []

    def diagnostic(err, host, port, driver, version):
        seen.append((type(err), host, port, driver, version))
        return "Connection refused (safe diagnostic)"

    with pytest.raises(RuntimeError, match="safe diagnostic") as raised:
        open_legacy_mysql(
            TARGET, driver="mysql.connector", decode_password=lambda _: SECRET,
            mysql_connector=Driver, connector_options=lambda *args: {},
            connector_diagnostic=diagnostic,
        )
    assert isinstance(raised.value.__cause__, DriverError)
    assert seen == [
        (DriverError, "rh.example", 3307, "mysql.connector", "9.5.0")
    ]


def test_mysqldb_driver_retains_utf8_long_and_ssl_options():
    operations = []
    conversions = {"other": str}
    certificates = {"ca": "ca.pem"}

    class Connection:
        def set_character_set(self, encoding):
            operations.append(("charset", encoding))

    class Driver:
        @staticmethod
        def connect(**kwargs):
            operations.append(("connect", kwargs.copy()))
            return Connection()

    conn, database = open_legacy_mysql(
        TARGET, driver="mysqldb", decode_password=lambda _: SECRET,
        certificates=certificates, mysqldb_driver=Driver,
        mysqldb_conversions=conversions, mysqldb_long_field=7,
    )
    assert isinstance(conn, Connection)
    assert database == "association_tdata"
    assert conversions == {"other": str, 7: int}
    assert operations == [
        ("connect", {
            "host": "rh.example", "user": "staff", "passwd": SECRET,
            "port": 3307, "use_unicode": True, "conv": conversions,
            "ssl": certificates,
        }),
        ("charset", "utf8"),
    ]


def test_mysqldb_charset_failure_closes_connection():
    operations = []

    class Connection:
        def set_character_set(self, _encoding):
            raise RuntimeError("charset unavailable")

        def close(self):
            operations.append("close")

    class Driver:
        @staticmethod
        def connect(**_kwargs):
            return Connection()

    with pytest.raises(RuntimeError, match="charset unavailable"):
        open_legacy_mysql(
            TARGET, driver="mysqldb", decode_password=lambda _: SECRET,
            mysqldb_driver=Driver, mysqldb_conversions={},
            mysqldb_long_field=7,
        )
    assert operations == ["close"]


@pytest.mark.parametrize(
    "driver,kwargs,error",
    [
        ("unsupported", {}, "Unsupported MySQL"),
        ("mysql.connector", {}, "mysql.connector is unavailable"),
        ("mysqldb", {}, "MySQLdb is unavailable"),
    ],
)
def test_invalid_or_unavailable_driver_fails_before_decoding(driver, kwargs, error):
    def forbid_decode(_token):
        pytest.fail("No password decoding without a selected connector")

    with pytest.raises((ValueError, RuntimeError), match=error):
        open_legacy_mysql(
            TARGET, driver=driver, decode_password=forbid_decode, **kwargs
        )


def test_target_must_be_parsed_not_a_raw_secret_bearing_reference():
    with pytest.raises(TypeError, match="parsed legacy"):
        open_legacy_mysql(
            "3306;host;user;secret[RESEAU]rh",
            driver="mysql.connector", decode_password=lambda x: x,
        )


def test_factory_has_no_gui_driver_or_teamworks_import():
    path = Path(__file__).resolve().parents[1] / "infrastructure/persistence/legacy_mysql_connection.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = {"wx", "wxPython", "PySide6", "PyQt5", "PyQt6",
                 "mysql", "MySQLdb", "GestionDB", "teamworks"}
    assert not any(name.split(".")[0] in forbidden for name in imports)
