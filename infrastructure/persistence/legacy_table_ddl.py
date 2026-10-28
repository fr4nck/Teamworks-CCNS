"""Compile Teamworks legacy SQLite/MySQL table DDL independently from UI.

SQL is returned, not executed. Identifier validation uses the same rules as
legacy table-copy operations. MySQL DDL can commit implicitly and therefore
cannot participate in the SQLite savepoint contract.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from infrastructure.persistence.legacy_table_transfer import legacy_sql_identifier

# Accept historical column type declarations, without SQL comments, separator,
# string literals, or multi-statement input. Not a generic SQL type parser.
_TYPE = re.compile(
    r"[A-Za-z][A-Za-z0-9_]*(?:\([0-9]+(?:,\s*[0-9]+)?\))?"
    r"(?: [A-Za-z][A-Za-z0-9_]*)*\Z"
)


def _validated_type(raw: str) -> str:
    if not isinstance(raw, str) or _TYPE.fullmatch(raw) is None:
        raise ValueError("Invalid legacy column type")
    return raw


def _legacy_type(raw: str, *, is_network: bool) -> str:
    _validated_type(raw)
    if not is_network:
        return {"LONGBLOB": "BLOB", "BIGINT": "INTEGER"}.get(raw, raw)
    aliases = {
        "INTEGER PRIMARY KEY AUTOINCREMENT": "INTEGER PRIMARY KEY AUTO_INCREMENT",
        "FLOAT": "REAL",
        "DATE": "VARCHAR(10)",
    }
    if raw in aliases:
        return aliases[raw]
    if raw.startswith("VARCHAR"):
        matched = re.fullmatch(r"VARCHAR\(([0-9]+)\)", raw)
        if matched is None:
            raise ValueError("Invalid legacy VARCHAR type")
        n = int(matched.group(1))
        if n > 20000:
            return "MEDIUMTEXT"
        if n > 255:
            return "TEXT(%d)" % n
    return raw


def legacy_create_table_query(
    table: str, descriptors: Iterable[tuple[str, str] | tuple], *, is_network: bool
) -> str:
    """Build one CREATE TABLE query preserving historical mapping and spacing."""
    validated = []
    for descriptor in descriptors:
        if len(descriptor) < 2:
            raise ValueError("Incomplete legacy column description")
        name = legacy_sql_identifier(descriptor[0])
        declared_type = _legacy_type(descriptor[1], is_network=is_network)
        validated.append("%s %s" % (name, declared_type))
    if not validated:
        raise ValueError("Cannot create a table without columns")
    return "CREATE TABLE %s (%s)" % (
        legacy_sql_identifier(table), ", ".join(validated)
    )


def legacy_add_column_query(table: str, column: str, type_name: str) -> str:
    return "ALTER TABLE %s ADD %s %s;" % (
        legacy_sql_identifier(table), legacy_sql_identifier(column),
        _validated_type(type_name),
    )


def legacy_drop_mysql_column_query(table: str, column: str) -> str:
    return "ALTER TABLE %s DROP %s;" % (
        legacy_sql_identifier(table), legacy_sql_identifier(column)
    )


def legacy_change_mysql_column_query(table: str, column: str, type_name: str) -> str:
    return "ALTER TABLE %s CHANGE %s %s %s;" % (
        legacy_sql_identifier(table), legacy_sql_identifier(column),
        legacy_sql_identifier(column), _validated_type(type_name),
    )


def legacy_create_index_query(index: str, table: str, column: str) -> str:
    return "CREATE INDEX %s ON %s (%s);" % (
        legacy_sql_identifier(index), legacy_sql_identifier(table),
        legacy_sql_identifier(column),
    )
