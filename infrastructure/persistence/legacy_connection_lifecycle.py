"""GUI-independent primitives for legacy SQLite and MySQL connection lifecycles.

The caller remains responsible for transaction boundaries, connection tracking
and user-facing diagnostics. Nothing commits on open or rolls back on close.
"""

from __future__ import annotations


def commit_if_connected(connection: object | None) -> None:
    """Commit an existing connection; preserve the legacy no-op for None."""
    if connection:
        connection.commit()


def close_if_connected(connection: object | None) -> None:
    """Close an existing connection, propagating a driver's errors to the caller."""
    if connection is not None:
        connection.close()
