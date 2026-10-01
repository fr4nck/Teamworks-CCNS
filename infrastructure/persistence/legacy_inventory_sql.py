"""Gabarits SQL partagés entre les adaptateurs d'inventaire historique.

Ce module ne fait que composer du texte SQL agrégé (COUNT/SUM/MIN/MAX) ;
il n'ouvre aucune connexion et ne connaît aucun moteur particulier au-delà
de la fonction de citation d'identifiant qu'on lui passe. Il permet
d'éviter de dupliquer la même logique d'agrégation entre l'adaptateur
SQLite et l'adaptateur MySQL, dont seule la syntaxe de citation et
d'introspection de schéma diffère réellement.
"""

from __future__ import annotations

from typing import Callable

from domain.migration.inventory_model import ColumnDefinition, ColumnKind

QuoteFn = Callable[[str], str]

_TEXT_LIKE_KINDS = (ColumnKind.TEXT, ColumnKind.UNKNOWN)
_NUMERIC_KINDS = (ColumnKind.INTEGER, ColumnKind.REAL)
_DATE_LIKE_KINDS = (ColumnKind.DATE, ColumnKind.DATETIME)


def build_column_stats_sql(*, table: str, column: ColumnDefinition, quote: QuoteFn) -> str:
    qtable = quote(table)
    qcol = quote(column.name)
    kind = column.kind

    parts = [
        "COUNT(*) AS row_count",
        f"SUM(CASE WHEN {qcol} IS NULL THEN 1 ELSE 0 END) AS null_count",
    ]

    if kind in _TEXT_LIKE_KINDS:
        parts.append(f"SUM(CASE WHEN {qcol} = '' THEN 1 ELSE 0 END) AS empty_count")
        parts.append(f"MIN(LENGTH({qcol})) AS min_len")
        parts.append(f"MAX(LENGTH({qcol})) AS max_len")
    else:
        parts.append("0 AS empty_count")
        parts.append("NULL AS min_len")
        parts.append("NULL AS max_len")

    if kind in _NUMERIC_KINDS:
        parts.append(f"SUM(CASE WHEN {qcol} = 0 THEN 1 ELSE 0 END) AS zero_count")
        parts.append(f"MIN({qcol}) AS min_num")
        parts.append(f"MAX({qcol}) AS max_num")
    else:
        parts.append("0 AS zero_count")
        parts.append("NULL AS min_num")
        parts.append("NULL AS max_num")

    if kind in _DATE_LIKE_KINDS:
        parts.append(f"MIN({qcol}) AS min_date")
        parts.append(f"MAX({qcol}) AS max_date")
    else:
        parts.append("NULL AS min_date")
        parts.append("NULL AS max_date")

    if kind is ColumnKind.BLOB:
        parts.append("NULL AS distinct_count")
    else:
        parts.append(f"COUNT(DISTINCT {qcol}) AS distinct_count")

    return f"SELECT {', '.join(parts)} FROM {qtable}"


def build_sample_values_sql(*, table: str, column: ColumnDefinition, quote: QuoteFn, limit: int) -> str:
    qtable = quote(table)
    qcol = quote(column.name)
    return (
        f"SELECT DISTINCT {qcol} FROM {qtable} "
        f"WHERE {qcol} IS NOT NULL AND {qcol} != '' "
        f"ORDER BY {qcol} LIMIT {int(limit)}"
    )


def build_row_count_sql(*, table: str, quote: QuoteFn) -> str:
    return f"SELECT COUNT(*) FROM {quote(table)}"


def build_duplicate_key_sql(*, table: str, key_columns: tuple[str, ...], quote: QuoteFn) -> str:
    qtable = quote(table)
    key_list = ", ".join(quote(name) for name in key_columns)
    return (
        f"SELECT COALESCE(SUM(surplus), 0) FROM ("
        f"SELECT COUNT(*) - 1 AS surplus FROM {qtable} "
        f"GROUP BY {key_list} HAVING COUNT(*) > 1"
        f") duplicated"
    )


def build_missing_key_sql(*, table: str, key_columns: tuple[str, ...], quote: QuoteFn) -> str:
    qtable = quote(table)
    condition = " OR ".join(f"{quote(name)} IS NULL" for name in key_columns)
    return f"SELECT COUNT(*) FROM {qtable} WHERE {condition}"


def build_select_rows_sql(*, table: str, columns: tuple[str, ...], quote: QuoteFn) -> str:
    qtable = quote(table)
    column_list = ", ".join(quote(name) for name in columns)
    return f"SELECT {column_list} FROM {qtable}"
