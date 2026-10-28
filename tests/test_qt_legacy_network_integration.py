"""Validate the Qt legacy adapter wiring without installing wx or accessing SQL.

Execute only the two functions under test from the source AST: the original
GestionDB module has many historic side effects and optional drivers.
"""

import ast
import base64
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.persistence.legacy_network_target import parse_legacy_network_target
from infrastructure.persistence.legacy_mysql_connection import open_legacy_mysql


SOURCE = Path(__file__).resolve().parents[1] / "teamworks/GestionDB.py"


def _load_legacy_function(name, *, db_method=False, globals_=None):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    nodes = tree.body
    if db_method:
        nodes = next(
            item.body for item in tree.body
            if isinstance(item, ast.ClassDef) and item.name == "DB"
        )
    function = next(
        item for item in nodes if isinstance(item, ast.FunctionDef) and item.name == name
    )
    scope = dict(globals_ or {})
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"), scope)
    return scope[name]


def test_qt_legacy_db_parameters_reuse_core_without_connecting():
    get_parameters = _load_legacy_function(
        "GetParamConnexionReseau", db_method=True,
        globals_={"parse_legacy_network_target": parse_legacy_network_target},
    )
    ref = "3306;rh.example;admin;#64#dGVzdA==[RESEAU]Sport_TDATA"
    db_without_driver = SimpleNamespace(nomFichier=ref)
    assert get_parameters(db_without_driver) == {
        "port": 3306,
        "hote": "rh.example",
        "host": "rh.example",
        "user": "admin",
        "utilisateur": "admin",
        "mdp": "#64#dGVzdA==",
        "password": "#64#dGVzdA==",
        "fichier": "sport_tdata",
    }


def test_qt_legacy_connection_passes_decoded_token_to_existing_mysql_adapter():
    calls = []

    class Connector:
        __version__ = "test"

        @staticmethod
        def connect(**options):
            calls.append(options)
            return "fake-connection"

    class MysqlOptions:
        @staticmethod
        def ConstruireOptionsConnexion(host, user, password, port, certs):
            return {
                "host": host, "user": user, "passwd": password,
                "port": int(port), "use_pure": True,
                "ssl_disabled": not bool(certs),
            }

    decode_password = _load_legacy_function(
        "DecodeMdpReseau", globals_={"base64": base64},
    )
    connect = _load_legacy_function(
        "GetConnexionReseau",
        globals_={
            "parse_legacy_network_target": parse_legacy_network_target,
            "open_legacy_mysql": open_legacy_mysql,
            "DecodeMdpReseau": decode_password,
            "INTERFACE_MYSQL": "mysql.connector",
            "IMPORT_MYSQLCONNECTOR_OK": True,
            "IMPORT_MYSQLDB_OK": False,
            "UTILS_MySQL": SimpleNamespace(
                ConstruireOptionsConnexion=MysqlOptions.ConstruireOptionsConnexion,
                FormaterDiagnosticConnexion=lambda *_args: "safe diagnostic",
            ),
            "mysql": SimpleNamespace(connector=Connector),
            "CERTIFICATS_SSL": {},
        },
    )
    connection, name = connect(
        "3307;db.local;operator;#64#c2VjcmV0[RESEAU]Sport_TDATA"
    )
    assert connection == "fake-connection"
    assert name == "sport_tdata"
    assert calls == [{
        "host": "db.local",
        "user": "operator",
        "passwd": "secret",
        "port": 3307,
        "use_pure": True,
        "ssl_disabled": True,
    }]


@pytest.mark.parametrize("name,method", [
    ("GetParamConnexionReseau", True),
    ("GetConnexionReseau", False),
])
def test_qt_legacy_adapter_invalid_reference_does_not_expose_secret(name, method):
    fn = _load_legacy_function(
        name,
        db_method=method,
        globals_={"parse_legacy_network_target": parse_legacy_network_target},
    )
    if method:
        invoke = lambda: fn(SimpleNamespace(nomFichier="notport;db;user;secret[RESEAU]RH"))
    else:
        invoke = lambda: fn("notport;db;user;secret[RESEAU]RH")
    with pytest.raises(ValueError) as error:
        invoke()
    assert "secret" not in str(error.value)


def test_qt_legacy_network_references_use_single_core_parser():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    db_class = next(
        item for item in tree.body
        if isinstance(item, ast.ClassDef) and item.name == "DB"
    )
    functions = [
        next(f for f in db_class.body if isinstance(f, ast.FunctionDef)
             and f.name == "GetParamConnexionReseau"),
        next(f for f in tree.body if isinstance(f, ast.FunctionDef)
             and f.name == "GetConnexionReseau"),
    ]
    for function in functions:
        calls = [
            node.func.id for node in ast.walk(function)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "parse_legacy_network_target" in calls


def test_qt_legacy_mysqldb_bridge_preserves_encoding_and_conversion():
    events = []
    my_conversions = {}
    class Connection:
        def set_character_set(self, charset):
            events.append(("charset", charset))

    class Driver:
        @staticmethod
        def connect(**kwargs):
            events.append(("connect", kwargs.copy()))
            return Connection()

    connect = _load_legacy_function(
        "GetConnexionReseau",
        globals_={
            "parse_legacy_network_target": parse_legacy_network_target,
            "open_legacy_mysql": open_legacy_mysql,
            "DecodeMdpReseau": lambda token: token,
            "INTERFACE_MYSQL": "mysqldb",
            "IMPORT_MYSQLCONNECTOR_OK": False,
            "IMPORT_MYSQLDB_OK": True,
            "UTILS_MySQL": SimpleNamespace(
                ConstruireOptionsConnexion=lambda *args: {},
                FormaterDiagnosticConnexion=lambda *args: "diagnostic",
            ),
            "MySQLdb": Driver,
            "conversions": my_conversions,
            "FIELD_TYPE": SimpleNamespace(LONG=3),
            "CERTIFICATS_SSL": {},
        },
    )
    connection, name = connect("3307;db.local;user;encoded[RESEAU]Sport_TDATA")
    assert isinstance(connection, Connection)
    assert name == "sport_tdata"
    assert events[0][0] == "connect"
    assert events[0][1]["port"] == 3307
    assert events[0][1]["passwd"] == "encoded"
    assert events[0][1]["conv"] is my_conversions
    assert my_conversions[3] is int
    assert events[1] == ("charset", "utf8")


def test_qt_legacy_mysql_driver_unavailable_fails_closed_without_decoding():
    connect = _load_legacy_function(
        "GetConnexionReseau",
        globals_={
            "parse_legacy_network_target": parse_legacy_network_target,
            "open_legacy_mysql": open_legacy_mysql,
            "DecodeMdpReseau": lambda _token: pytest.fail("decoding forbidden"),
            "INTERFACE_MYSQL": "mysql.connector",
            "IMPORT_MYSQLCONNECTOR_OK": False,
            "IMPORT_MYSQLDB_OK": False,
            "UTILS_MySQL": SimpleNamespace(
                ConstruireOptionsConnexion=lambda *_args: {},
                FormaterDiagnosticConnexion=lambda *_args: "",
            ),
            "CERTIFICATS_SSL": {},
        },
    )
    with pytest.raises(RuntimeError, match="mysql.connector is unavailable"):
        connect("3306;db.local;user;secret[RESEAU]RH")


def test_qt_mysql_connection_is_a_headless_core_delegation():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(node for node in tree.body
              if isinstance(node, ast.FunctionDef) and node.name == "GetConnexionReseau")
    direct_calls = [
        node.func.id for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert "open_legacy_mysql" in direct_calls
    assert "parse_legacy_network_target" in direct_calls
    assert "DecodeMdpReseau" not in direct_calls
    assert "GetConnexionReseau" not in direct_calls
