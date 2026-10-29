"""Diagnostic MySQL étape par étape, en lecture seule et sans secret.

Distingue l'accès TCP, la négociation MySQL, l'authentification, la sélection
de la base et la compatibilité du schéma. Aucune écriture : seuls ``USE``,
``SELECT`` et ``SHOW`` sont exécutés. Ni la référence réseau complète, ni le jeton du
mot de passe, ni le mot de passe décodé n'apparaissent dans le rapport.
Le pilote, l'ouverture de connexion et le contrôle de schéma sont injectés :
aucune dépendance à wx, Qt ou GestionDB ici.
"""

from __future__ import annotations

import importlib
import socket
import struct
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from infrastructure.persistence.legacy_mysql_schema import activate_legacy_mysql_schema
from infrastructure.persistence.legacy_network_target import parse_legacy_network_target

OK = "OK"
ECHEC = "ÉCHEC"
NON_TESTE = "NON TESTÉ"

STEP_NAMES = (
    "TCP",
    "Négociation MySQL",
    "Authentification",
    "Sélection de la base",
    "Compatibilité du schéma",
)

# Modules chargés dynamiquement par mysql.connector : absents d'un exe mal construit.
DYNAMIC_DRIVER_MODULES = (
    "mysql.connector.locales.eng.client_error",
    "mysql.connector.plugins.mysql_native_password",
    "mysql.connector.plugins.caching_sha2_password",
    "mysql.connector.plugins.sha256_password",
)

_AUTH_PLUGIN_ERRORS = {1251, 2059, 2061}
_HANDSHAKE_ERRORS = {2013, 2055}
_TCP_ERRORS = {2003, 2005}


@dataclass(frozen=True)
class StepResult:
    name: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class DiagnosticReport:
    target: str
    header: tuple[str, ...]
    steps: tuple[StepResult, ...]

    @property
    def ok(self) -> bool:
        return all(step.status == OK for step in self.steps)

    def text(self) -> str:
        lines = list(self.header)
        lines.append("Cible : " + self.target)
        lines.append("")
        for index, step in enumerate(self.steps, start=1):
            lines.append(f"{index}. {step.name} : {step.status}" + (f" — {step.detail}" if step.detail else ""))
        lines.append("")
        failed = next((step.name for step in self.steps if step.status == ECHEC), None)
        lines.append("Aucune écriture n'a été effectuée (requêtes exécutées : USE, SELECT et SHOW uniquement).")
        lines.append("Résultat : CONFORME" if self.ok else f"Résultat : NON CONFORME — première étape en échec : {failed}")
        return "\n".join(lines) + "\n"


def embedded_driver_lines(connector: Any) -> tuple[str, ...]:
    """Décrit le pilote réellement importé, y compris ses modules dynamiques."""
    if connector is None:
        return ("Pilote : mysql.connector ABSENT de cette application",)
    version = getattr(connector, "__version__", "inconnue")
    missing = []
    for name in DYNAMIC_DRIVER_MODULES:
        try:
            importlib.import_module(name)
        except Exception:
            missing.append(name.rsplit(".", 1)[-1] if "plugins" in name else "traductions d'erreurs (eng)")
    lines = [f"Pilote : mysql.connector {version} (mode Python pur)"]
    lines.append(
        "Modules dynamiques du pilote : tous présents (traductions d'erreurs, "
        "mysql_native_password, caching_sha2_password, sha256_password)"
        if not missing else "Modules dynamiques du pilote MANQUANTS : " + ", ".join(missing)
    )
    return tuple(lines)


def _read_exact(sock: socket.socket, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("connexion fermée par le serveur pendant la négociation")
        data += chunk
    return data


def parse_greeting(payload: bytes) -> dict[str, Any]:
    """Analyse le paquet d'accueil MySQL (protocole 10) ou son paquet d'erreur."""
    if not payload:
        raise ValueError("paquet d'accueil vide")
    if payload[0] == 0xFF:
        errno = struct.unpack_from("<H", payload, 1)[0]
        message = payload[3:]
        if message[:1] == b"#":
            message = message[6:]
        return {"error": errno, "message": message.decode("utf-8", "replace")}
    if payload[0] != 10:
        raise ValueError(f"protocole MySQL {payload[0]} non pris en charge")
    end = payload.index(b"\0", 1)
    version = payload[1:end].decode("utf-8", "replace")
    pos = end + 1 + 4 + 8 + 1
    capabilities = struct.unpack_from("<H", payload, pos)[0]
    pos += 2
    plugin = ""
    if len(payload) > pos:
        pos += 1 + 2
        capabilities |= struct.unpack_from("<H", payload, pos)[0] << 16
        pos += 2
        auth_len = payload[pos]
        pos += 1 + 10
        if capabilities & 0x00008000:  # CLIENT_SECURE_CONNECTION
            pos += max(13, auth_len - 8)
        if capabilities & 0x00080000 and pos < len(payload):  # CLIENT_PLUGIN_AUTH
            plugin = payload[pos:].split(b"\0", 1)[0].decode("ascii", "replace")
    return {
        "version": version,
        "tls": bool(capabilities & 0x00000800),
        "plugin": plugin or "(non annoncée)",
    }


def _probe_tcp_and_greeting(host: str, port: int, timeout: float):
    """Étapes 1 et 2 : connexion TCP puis lecture passive de l'accueil MySQL.

    Rien n'est envoyé au serveur ; la connexion est refermée aussitôt.
    """
    started = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
    except OSError as exc:
        return StepResult(STEP_NAMES[0], ECHEC, f"{host}:{port} injoignable ({type(exc).__name__}: {exc})"), None
    elapsed = (time.perf_counter() - started) * 1000
    tcp = StepResult(STEP_NAMES[0], OK, f"{host}:{port} joignable en {elapsed:.0f} ms")
    try:
        with sock:
            sock.settimeout(timeout)
            header = _read_exact(sock, 4)
            length = header[0] | header[1] << 8 | header[2] << 16
            greeting = parse_greeting(_read_exact(sock, length))
    except Exception as exc:
        return tcp, StepResult(STEP_NAMES[1], ECHEC, f"accueil MySQL illisible ({type(exc).__name__}: {exc})")
    if "error" in greeting:
        return tcp, StepResult(
            STEP_NAMES[1], ECHEC,
            f"le serveur refuse la connexion avant authentification (code MySQL {greeting['error']} : {greeting['message']})",
        )
    return tcp, StepResult(
        STEP_NAMES[1], OK,
        f"serveur MySQL {greeting['version']}, authentification annoncée {greeting['plugin']}, "
        f"TLS proposé par le serveur : {'oui' if greeting['tls'] else 'non'}",
    )


def _error_code(exc: BaseException) -> int | None:
    for candidate in (exc, exc.__cause__, exc.__context__):
        errno = getattr(candidate, "errno", None)
        if isinstance(errno, int):
            return errno
    return None


def _authentication_failure(exc: BaseException) -> StepResult:
    errno = _error_code(exc)
    first_line = str(exc).strip().splitlines()
    detail = " · ".join(line.strip() for line in first_line if line.strip()) or type(exc).__name__
    if errno == 1045:
        cause = "identifiant ou mot de passe refusé par le serveur"
    elif errno in _AUTH_PLUGIN_ERRORS:
        cause = "méthode d'authentification du compte non prise en charge par le pilote"
    elif errno in _HANDSHAKE_ERRORS:
        cause = "connexion interrompue pendant la négociation"
    elif errno in _TCP_ERRORS:
        cause = "serveur injoignable lors de la connexion du pilote"
    elif errno == 2026:
        cause = "échec de la négociation TLS"
    else:
        cause = "connexion du pilote impossible"
    return StepResult(STEP_NAMES[2], ECHEC, f"{cause} ({detail})")


def _scrub(text: str, secrets: tuple[str, ...]) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "<masqué>")
    return text


def run_mysql_diagnostic(
    reference: str,
    *,
    suffix: str = "TDATA",
    connector: Any,
    open_connection: Callable[[str], tuple[Any, str]],
    check_schema: Callable[[], Any],
    decode_password: Callable[[str], str],
    tls_label: str,
    application_label: str = "Teamworks Qt",
    timeout: float = 5.0,
    now: datetime | None = None,
) -> DiagnosticReport:
    """Exécute les cinq étapes dans l'ordre ; une étape en échec arrête les suivantes."""
    reference_with_suffix = f"{reference}_{suffix}" if suffix else reference
    target = parse_legacy_network_target(reference_with_suffix)
    secrets = tuple(s for s in (target.password_token, decode_password(target.password_token)) if len(s or "") >= 3)
    header = (
        f"Diagnostic MySQL {application_label} — lecture seule",
        "Date : " + (now or datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
        *embedded_driver_lines(connector),
        "Chiffrement côté client : " + tls_label,
    )
    label = f"base « {target.database} » sur {target.host}:{target.port} · utilisateur {target.user}"
    steps: list[StepResult] = []

    def finish() -> DiagnosticReport:
        while len(steps) < len(STEP_NAMES):
            steps.append(StepResult(STEP_NAMES[len(steps)], NON_TESTE))
        cleaned = tuple(StepResult(s.name, s.status, _scrub(s.detail, secrets)) for s in steps)
        return DiagnosticReport(_scrub(label, secrets), tuple(_scrub(h, secrets) for h in header), cleaned)

    tcp, greeting = _probe_tcp_and_greeting(target.host, target.port, timeout)
    steps.append(tcp)
    if tcp.status != OK:
        return finish()
    steps.append(greeting)
    if greeting.status != OK:
        return finish()

    try:
        connection, database = open_connection(reference_with_suffix)
    except Exception as exc:
        steps.append(_authentication_failure(exc))
        return finish()
    try:
        cursor = connection.cursor()
        server = getattr(connection, "get_server_info", lambda: "")() or ""
        steps.append(StepResult(STEP_NAMES[2], OK, f"compte « {target.user} » accepté" + (f" par MySQL {server}" if server else "")))
        try:
            activate_legacy_mysql_schema(cursor, database)
            cursor.execute(
                "SELECT VERSION(), @@character_set_server, @@collation_server, "
                "@@character_set_connection, @@collation_connection"
            )
            version, cs_server, coll_server, cs_conn, coll_conn = cursor.fetchone()
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s",
                (database,),
            )
            tables = cursor.fetchone()[0]
        except Exception as exc:
            errno = _error_code(exc)
            cause = {1049: "base inexistante sur ce serveur", 1044: "accès à la base refusé pour ce compte"}.get(
                errno, "sélection impossible"
            )
            steps.append(StepResult(STEP_NAMES[3], ECHEC, f"« {database} » : {cause} ({type(exc).__name__}: {exc})"))
            return finish()
        steps.append(StepResult(
            STEP_NAMES[3], OK,
            f"« {database} » ouverte, {tables} tables ; serveur {version}, "
            f"jeu de caractères serveur {cs_server}/{coll_server}, connexion {cs_conn}/{coll_conn}",
        ))
    finally:
        try:
            connection.close()
        except Exception:
            pass

    try:
        report = check_schema()
    except Exception as exc:
        steps.append(StepResult(STEP_NAMES[4], ECHEC, f"contrôle impossible ({type(exc).__name__}: {exc})"))
        return finish()
    if getattr(report, "compatible", False):
        steps.append(StepResult(STEP_NAMES[4], OK, report.summary().replace("\n", " ")))
    else:
        text = report.blocking_text() if hasattr(report, "blocking_text") else str(report)
        steps.append(StepResult(STEP_NAMES[4], ECHEC, text.replace("\n", " ")))
    return finish()
