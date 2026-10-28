"""GUI-free MySQL schema activation for historical Teamworks connections.

No driver is imported. Selection and creation are explicit, and this helper
never commits or rolls back the caller's transaction.
"""

from __future__ import annotations

from typing import Any


def quote_mysql_schema_name(name: str) -> str:
    """Safely quote a MySQL 5.5-compatible schema identifier.

    Preserve ordinary historical names, including names with hyphens or
    spaces. Reject disallowed database-name characters and control bytes
    before executing any SQL. Do not echo untrusted identifiers in errors.
    """
    if not isinstance(name, str) or not name or len(name) > 64:
        raise ValueError("Invalid MySQL schema name")
    if name != name.strip() or any(
        ch in name for ch in ("\x00", "/", "\\", ".", ";")
    ) or any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ValueError("Invalid MySQL schema name")
    return "\x60" + name.replace("\x60", "\x60\x60") + "\x60"


def mysql_schema_commands(
    name: str | None, *, allow_creation: bool = False
) -> tuple[str, ...]:
    """Build the same legacy CREATE/USE sequence without side effects.

    An empty database and the historical _tdata sentinel skip USE in
    normal connection mode. Explicit creation still creates _tdata
    (as in GestionDB) but never creates an empty-name schema.
    """
    if name in (None, ""):
        if allow_creation:
            raise ValueError("A schema name is required for creation")
        return ()

    quoted = quote_mysql_schema_name(name)
    queries: list[str] = []
    if allow_creation:
        queries.append(
            "CREATE DATABASE IF NOT EXISTS %s CHARSET utf8 COLLATE utf8_unicode_ci;"
            % quoted
        )
    if name != "_tdata":
        queries.append("USE %s;" % quoted)
    return tuple(queries)


def activate_legacy_mysql_schema(
    cursor: Any, name: str | None, *, allow_creation: bool = False
) -> None:
    """Execute only the requested CREATE/USE statements, in original order."""
    for sql in mysql_schema_commands(name, allow_creation=allow_creation):
        cursor.execute(sql)
