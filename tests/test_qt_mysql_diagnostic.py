"""Diagnostic MySQL Qt : cinq étapes distinctes, lecture seule, aucun secret.

Les serveurs sont simulés sur 127.0.0.1 avec le vrai protocole MySQL (accueil
5.7.31, erreurs serveur) ; aucune base réelle n'est contactée.
"""
from __future__ import annotations

import importlib.util
import socket
import struct
import sys
import threading
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.persistence.legacy_mysql_connection import open_legacy_mysql  # noqa: E402
from infrastructure.persistence.legacy_network_target import parse_legacy_network_target  # noqa: E402
from infrastructure.persistence.mysql_connection_diagnostic import (  # noqa: E402
    ECHEC,
    NON_TESTE,
    OK,
    parse_greeting,
    run_mysql_diagnostic,
)

PASSWORD = "mdp-fictif-recette"
TOKEN = "#64#bWRwLWZpY3RpZi1yZWNldHRl"  # base64 de PASSWORD


def _decode(token):
    import base64

    return base64.b64decode(token[4:]).decode() if token.startswith("#64#") else token


def _utils_mysql():
    spec = importlib.util.spec_from_file_location("utils_mysql_diag", ROOT / "teamworks" / "Utils" / "UTILS_MySQL.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packet(payload: bytes, seq: int) -> bytes:
    return struct.pack("<I", len(payload))[:3] + bytes([seq]) + payload


def _greeting(version=b"5.7.31-log") -> bytes:
    caps = 0x1 | 0x2 | 0x4 | 0x8 | 0x200 | 0x2000 | 0x8000 | 0x10000 | 0x20000 | 0x80000
    return (
        b"\x0a" + version + b"\0" + struct.pack("<I", 7) + b"abcdefgh" + b"\0"
        + struct.pack("<H", caps & 0xFFFF) + bytes([33]) + struct.pack("<H", 2)
        + struct.pack("<H", caps >> 16) + bytes([21]) + b"\0" * 10
        + b"ijklmnopqrst\0" + b"mysql_native_password\0"
    )


def _error(errno: int, state: bytes, message: bytes) -> bytes:
    return b"\xff" + struct.pack("<H", errno) + b"#" + state + message


class FakeMysqlServer:
    """Accueil MySQL 5.7.31 puis refus de l'authentification (1045), ou refus d'hôte."""

    def __init__(self, mode="deny-auth"):
        self.mode = mode
        self.received = []
        self._sock = socket.socket()
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(4)
        self._sock.settimeout(10)
        self.port = self._sock.getsockname()[1]
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        try:
            while True:
                conn, _ = self._sock.accept()
                with conn:
                    conn.settimeout(10)
                    if self.mode == "refuse-host":
                        conn.sendall(_packet(_error(1130, b"HY000", b"Host '127.0.0.1' is not allowed to connect"), 0))
                        continue
                    conn.sendall(_packet(_greeting(), 0))
                    header = conn.recv(4)
                    if len(header) < 4:
                        continue  # sonde passive du diagnostic : rien n'est envoyé
                    size = header[0] | header[1] << 8 | header[2] << 16
                    body = b""
                    while len(body) < size:
                        body += conn.recv(size - len(body))
                    self.received.append(body)
                    message = b"Access denied for user 'recette'@'localhost' (using password: YES)"
                    conn.sendall(_packet(_error(1045, b"28000", message), header[3] + 1))
        except OSError:
            pass

    def close(self):
        self._sock.close()


@pytest.fixture
def server(request):
    instance = FakeMysqlServer(getattr(request, "param", "deny-auth"))
    yield instance
    instance.close()


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _connector_or_skip():
    return pytest.importorskip("mysql.connector")


def _open_with_real_connector(reference):
    connector = _connector_or_skip()
    utils = _utils_mysql()
    return open_legacy_mysql(
        parse_legacy_network_target(reference),
        driver="mysql.connector",
        decode_password=_decode,
        certificates={},
        mysql_connector=connector,
        connector_options=utils.ConstruireOptionsConnexion,
        connector_diagnostic=utils.FormaterDiagnosticConnexion,
    )


def _diagnose(port, **overrides):
    options = dict(
        connector=None,
        open_connection=_open_with_real_connector,
        check_schema=lambda: pytest.fail("schéma contrôlé alors qu'une étape précédente a échoué"),
        decode_password=_decode,
        tls_label="désactivé",
        timeout=3,
        now=datetime(2026, 10, 29, 12, 0, 0),
    )
    options.update(overrides)
    return run_mysql_diagnostic(f"{port};127.0.0.1;recette;{TOKEN}[RESEAU]recette", **options)


def _assert_no_secret(text):
    assert TOKEN not in text and TOKEN[4:] not in text
    assert PASSWORD not in text
    assert "[RESEAU]" not in text


def test_greeting_parser_reads_version_plugin_and_server_errors():
    info = parse_greeting(_greeting())
    assert info == {"version": "5.7.31-log", "tls": False, "plugin": "mysql_native_password"}
    refused = parse_greeting(_error(1130, b"HY000", b"Host 'x' is not allowed to connect"))
    assert refused["error"] == 1130 and "not allowed" in refused["message"]


def test_closed_port_fails_at_tcp_and_stops(tmp_path):
    report = _diagnose(_free_port())
    assert [s.status for s in report.steps] == [ECHEC, NON_TESTE, NON_TESTE, NON_TESTE, NON_TESTE]
    assert "première étape en échec : TCP" in report.text()
    _assert_no_secret(report.text())


@pytest.mark.parametrize("server", ["refuse-host"], indirect=True)
def test_host_refused_before_authentication_is_a_negotiation_failure(server):
    report = _diagnose(server.port)
    assert [s.status for s in report.steps[:3]] == [OK, ECHEC, NON_TESTE]
    assert "1130" in report.steps[1].detail
    _assert_no_secret(report.text())


def test_rejected_password_with_real_connector_is_an_authentication_failure(server):
    connector = _connector_or_skip()
    report = _diagnose(server.port, connector=connector)
    text = report.text()
    assert [s.status for s in report.steps] == [OK, OK, ECHEC, NON_TESTE, NON_TESTE]
    assert "serveur MySQL 5.7.31-log" in report.steps[1].detail
    assert "mysql_native_password" in report.steps[1].detail
    assert "identifiant ou mot de passe refusé" in report.steps[2].detail
    assert "1045" in report.steps[2].detail
    assert "ImportError" not in text and "localization" not in text
    assert "Modules dynamiques du pilote : tous présents" in text
    assert f"mysql.connector {connector.__version__}" in text
    # Le pilote a bien négocié en mysql_native_password, attendu par MySQL 5.7.
    assert server.received and b"mysql_native_password" in server.received[0]
    _assert_no_secret(text)


def test_real_connector_client_error_is_readable_without_secret():
    _connector_or_skip()
    with pytest.raises(RuntimeError) as caught:
        _open_with_real_connector(f"{_free_port()};127.0.0.1;recette;{TOKEN}[RESEAU]recette")
    message = str(caught.value)
    assert "Connexion MySQL impossible." in message and "2003" in message
    assert "ImportError" not in message and "localization" not in message
    _assert_no_secret(message)


class _RecordingCursor:
    def __init__(self, log):
        self.log = log
        self._row = None

    def execute(self, sql, params=()):
        self.log.append(sql)
        if sql.startswith("SELECT VERSION()"):
            self._row = ("5.7.31-log", "utf8", "utf8_general_ci", "utf8", "utf8_general_ci")
        elif "information_schema.TABLES" in sql:
            self._row = (96,)

    def fetchone(self):
        return self._row


class _FakeConnection:
    def __init__(self):
        self.log = []
        self.closed = False

    def cursor(self):
        return _RecordingCursor(self.log)

    def get_server_info(self):
        return "5.7.31-log"

    def close(self):
        self.closed = True


class _Compatible:
    compatible = True

    def summary(self):
        return "Base compatible avec Teamworks Qt."


class _Incompatible:
    compatible = False

    def blocking_text(self):
        return "Table « presences » absente."


def test_complete_success_runs_only_reads_and_closes_the_connection(server):
    connection = _FakeConnection()
    report = _diagnose(
        server.port,
        open_connection=lambda reference: (connection, parse_legacy_network_target(reference).database),
        check_schema=lambda: _Compatible(),
    )
    assert report.ok, report.text()
    assert all(sql.split()[0].upper() in ("USE", "SELECT") for sql in connection.log)
    assert connection.log[0] == "USE `recette_tdata`;"
    assert connection.closed
    assert "« recette_tdata » ouverte, 96 tables" in report.steps[3].detail
    assert report.text().endswith("Résultat : CONFORME\n")
    _assert_no_secret(report.text())


def test_incompatible_schema_is_reported_at_the_last_step(server):
    report = _diagnose(
        server.port,
        open_connection=lambda reference: (_FakeConnection(), "recette_tdata"),
        check_schema=lambda: _Incompatible(),
    )
    assert [s.status for s in report.steps] == [OK, OK, OK, OK, ECHEC]
    assert "presences" in report.steps[4].detail


def test_unknown_database_is_a_selection_failure(server):
    class UnknownDb(Exception):
        errno = 1049

    class Cursor(_RecordingCursor):
        def execute(self, sql, params=()):
            raise UnknownDb("1049 (42000): Unknown database 'recette_tdata'")

    connection = _FakeConnection()
    connection.cursor = lambda: Cursor(connection.log)
    report = _diagnose(server.port, open_connection=lambda reference: (connection, "recette_tdata"))
    assert [s.status for s in report.steps] == [OK, OK, OK, ECHEC, NON_TESTE]
    assert "base inexistante" in report.steps[3].detail
    assert connection.closed


def test_launcher_command_writes_a_new_report_without_secret(monkeypatch, tmp_path):
    """Chemin réel de l'exe : Config.json → GestionDB → rapport ; aucune base contactée."""
    pytest.importorskip("appdirs")  # GestionDB réel (job Windows natif)
    pytest.importorskip("PySide6")
    for path in (ROOT / "poc" / "qt-theme", ROOT / "teamworks"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    import launcher
    from Utils import UTILS_Fichiers

    config = tmp_path / "Config.json"
    config.write_text('{"nomFichier": "%d;127.0.0.1;recette;%s[RESEAU]recette"}' % (_free_port(), TOKEN), encoding="utf-8")
    monkeypatch.setattr(UTILS_Fichiers, "GetRepUtilisateur", lambda name="": str(tmp_path / name))
    monkeypatch.setattr(launcher, "import_chemins_safely", lambda: None)
    monkeypatch.setenv("TEAMWORKS_QT_AUTOCLOSE_MS", "100")
    monkeypatch.setenv("TEAMWORKS_QT_DIAGNOSTIC_DIR", str(tmp_path))
    (tmp_path / "diagnostic-mysql-existant.txt").write_text("à conserver", encoding="utf-8")

    assert launcher.run_mysql_diagnostic_command(None) == 6
    reports = sorted(p for p in tmp_path.glob("diagnostic-mysql-2*.txt"))
    assert len(reports) == 1
    text = reports[0].read_text(encoding="utf-8")
    assert "1. TCP : ÉCHEC" in text and "Configuration lue : " in text
    assert "Modules dynamiques du pilote : tous présents" in text
    _assert_no_secret(text)
    assert (tmp_path / "diagnostic-mysql-existant.txt").read_text(encoding="utf-8") == "à conserver"
    assert launcher.run_mysql_diagnostic_command(None) == 6
    assert len(list(tmp_path.glob("diagnostic-mysql-2*.txt"))) == 2


def test_a_secret_leaked_by_a_driver_message_is_masked(server):
    def leaky(reference):
        raise RuntimeError(f"échec avec {PASSWORD} et {TOKEN}")

    text = _diagnose(server.port, open_connection=leaky).text()
    assert "<masqué>" in text
    _assert_no_secret(text)
