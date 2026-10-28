"""Headless legacy SQL batch execution with an explicit commit boundary.

This is a compatibility helper, not a replacement for the newer atomic
contract-writing transaction service. Existing legacy placeholder conversion
and commit behavior must remain unchanged until migrated and qualified.
"""

from __future__ import annotations

from typing import Any, Iterable


def legacy_batch_query(query: str, *, is_network: bool) -> str:
    """Translate placeholders exactly like GestionDB.Executermany."""
    if is_network:
        return query.replace("?", "%s")
    return query.replace("%s", "?")


def execute_legacy_batch(
    cursor: Any,
    connection: Any,
    query: str,
    rows: Iterable[Any],
    *,
    is_network: bool,
    commit: bool = True,
) -> None:
    """Execute one batch, commit only when requested, and never auto-rollback.

    Return and exception behavior is delegated to the underlying cursor.
    The caller owns rollback on failure, preserving the historical contract.
    """
    cursor.executemany(legacy_batch_query(query, is_network=is_network), rows)
    if commit == True:
        connection.commit()
