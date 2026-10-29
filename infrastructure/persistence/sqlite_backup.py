"""Sauvegarde et restauration isolée des fichiers SQLite Teamworks.

* La sauvegarde utilise l'API ``backup`` de SQLite (copie cohérente d'une base
  ouverte) vers un nom réservé en création exclusive : deux sauvegardes
  rapprochées ne peuvent jamais partager un fichier.
* La restauration ne cible jamais la base active : elle produit une copie
  vérifiée dans un fichier neuf, que l'utilisateur substitue lui-même, base
  fermée, s'il le décide.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SqliteCopyCheck:
    integrity: str
    row_counts: dict[str, int]
    content_digest: str


def reserve_unique_path(base: str, label: str, *, now: datetime | None = None) -> str:
    """Crée un fichier vide au nom unique ``<base>.<label>-<horodatage>[-n].bak``."""
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S-%f")
    for index in range(1, 1000):
        suffix = "" if index == 1 else "-%d" % index
        candidate = "%s.%s-%s%s.bak" % (base, label, stamp, suffix)
        try:
            os.close(os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        except FileExistsError:
            continue
        return candidate
    raise RuntimeError("Impossible de réserver un nom de sauvegarde unique pour %s" % base)


def inspect_sqlite_copy(connection) -> SqliteCopyCheck:
    """Intégrité, effectifs et empreinte du contenu de toutes les tables utilisateur."""
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    digest = hashlib.sha256()
    counts = {}
    for table in tables:
        rows = connection.execute('SELECT * FROM "%s" ORDER BY rowid' % table).fetchall()
        counts[table] = len(rows)
        digest.update(table.encode("utf-8"))
        digest.update(repr(rows).encode("utf-8"))
    return SqliteCopyCheck(integrity, counts, digest.hexdigest())


def backup_open_sqlite(connection, source_path: str, label: str, *, now: datetime | None = None) -> str:
    """Copie la base ouverte vers un fichier neuf, puis vérifie la copie."""
    if not source_path or not os.path.isfile(source_path):
        raise RuntimeError("Fichier SQLite introuvable : sauvegarde impossible.")
    base, _ext = os.path.splitext(source_path)
    target = reserve_unique_path(base, label, now=now)
    destination = sqlite3.connect(target)
    try:
        connection.backup(destination)
        destination.commit()
        copy = inspect_sqlite_copy(destination)
        if copy.integrity != "ok":
            raise RuntimeError("Sauvegarde corrompue : %s" % copy.integrity)
        if copy != inspect_sqlite_copy(connection):
            raise RuntimeError("Sauvegarde incomplète : contenu différent de la base.")
    finally:
        destination.close()
    return target


def restore_sqlite_backup(backup_path: str, destination_path: str, *, active_paths=()) -> SqliteCopyCheck:
    """Restaure une sauvegarde dans un fichier neuf, jamais sur une base active.

    Refuse une destination existante ou désignant une base active ; vérifie que
    la copie restaurée est intègre et identique, table par table, à la sauvegarde.
    """
    if not os.path.isfile(backup_path):
        raise ValueError("Sauvegarde introuvable : %s" % backup_path)
    destination = os.path.normcase(os.path.abspath(destination_path))
    for active in active_paths:
        if active and os.path.normcase(os.path.abspath(active)) == destination:
            raise ValueError("Restauration refusée : la destination est la base active.")
    if os.path.normcase(os.path.abspath(backup_path)) == destination:
        raise ValueError("Restauration refusée : la destination est la sauvegarde elle-même.")
    try:
        os.close(os.open(destination_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        raise ValueError("Restauration refusée : %s existe déjà." % destination_path) from None

    try:
        restored, expected = _copy_backup(backup_path, destination_path)
        if restored != expected:
            raise RuntimeError("Restauration incohérente : contenu différent de la sauvegarde.")
    except BaseException:
        # Seul le fichier neuf réservé ci-dessus est retiré : rien d'existant n'est touché.
        try:
            os.remove(destination_path)
        except OSError:
            pass
        raise
    return restored


def _copy_backup(backup_path: str, destination_path: str):
    source = sqlite3.connect(Path(backup_path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        expected = inspect_sqlite_copy(source)
        if expected.integrity != "ok":
            raise RuntimeError("Sauvegarde corrompue : %s" % expected.integrity)
        target = sqlite3.connect(destination_path)
        try:
            source.backup(target)
            target.commit()
            restored = inspect_sqlite_copy(target)
        finally:
            target.close()
    finally:
        source.close()
    return restored, expected
