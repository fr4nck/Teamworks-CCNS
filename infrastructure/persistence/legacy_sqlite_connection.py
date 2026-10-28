"""Open historic Teamworks SQLite files without any graphical toolkit.

Unlike newly created repositories, the legacy SQLite path must not create an
absent database during ordinary reads. Creation is an explicit caller choice.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Callable


def open_legacy_sqlite(
    path: str | os.PathLike[str],
    *,
    allow_creation: bool = False,
    connect: Callable[..., sqlite3.Connection] = sqlite3.connect,
) -> tuple[sqlite3.Connection, sqlite3.Cursor] | None:
    """Return (connection, cursor), or None for a missing read-only target.

    Keep the default sqlite3 settings used by historical GestionDB. No
    directory creation, schema migration, pragma, commit or UI callback occurs.
    A connection is closed if cursor construction unexpectedly fails.
    """
    if not allow_creation and not os.path.isfile(path):
        return None

    connection = connect(path)
    try:
        cursor = connection.cursor()
    except BaseException:
        try:
            connection.close()
        except Exception:
            pass
        raise
    return connection, cursor
