"""Évolution additive contrôlée des colonnes CCNS de la table ``contrats``.

Seule opération de schéma que Teamworks Qt peut effectuer, et uniquement :

* sur demande explicite de l'utilisateur (confirmation dans l'interface) ;
* sur une base déclarée compatible par ``check_schema`` ;
* sur un fichier SQLite local, après une copie de sauvegarde vérifiée ;
* par ajout de colonnes vides (``ALTER TABLE ... ADD COLUMN``), sans
  conversion ni modification d'aucune ligne existante.

Les bases réseau MySQL sont refusées : aucune sauvegarde automatique n'y est
possible depuis le poste, l'ajout relève de l'administrateur ou de
Teamworks wx (page Contrats). ``UpgradeDB`` n'est jamais appelé.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from infrastructure.persistence.qt_schema_compatibility import (
    CONTRACT_ENGINE_COLUMNS,
    check_schema,
)

_COUNTED_TABLES = ("personnes", "contrats", "contrats_valchamps")


@dataclass(frozen=True)
class ContractSchemaEvolution:
    ok: bool
    message: str
    created: tuple[str, ...] = ()
    backup_path: str | None = None


def _row_counts(connection) -> dict[str, int]:
    return {
        table: int(connection.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0])
        for table in _COUNTED_TABLES
    }


def _contracts_fingerprint(connection, columns: tuple[str, ...]) -> int:
    select = ", ".join('"%s"' % name for name in columns)
    rows = connection.execute('SELECT %s FROM contrats ORDER BY IDcontrat' % select).fetchall()
    return hash(tuple(rows))


def backup_sqlite(db, *, now: datetime | None = None) -> str:
    """Copie cohérente du fichier SQLite ouvert (API backup), puis contrôle d'intégrité."""
    source_path = str(getattr(db, "nomFichier", "") or "")
    if not source_path or not os.path.isfile(source_path):
        raise RuntimeError("Fichier SQLite introuvable : sauvegarde impossible.")
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    base, _ext = os.path.splitext(source_path)
    target = "%s.avant-colonnes-ccns-%s.bak" % (base, stamp)
    if os.path.exists(target):
        raise RuntimeError("Une sauvegarde porte déjà ce nom : %s" % target)
    destination = sqlite3.connect(target)
    try:
        db.connexion.backup(destination)
        destination.commit()
        status = destination.execute("PRAGMA integrity_check").fetchone()[0]
        if status != "ok":
            raise RuntimeError("Sauvegarde corrompue : %s" % status)
        if _row_counts(destination) != _row_counts(db.connexion):
            raise RuntimeError("Sauvegarde incomplète : effectifs différents.")
    finally:
        destination.close()
    return target


def add_contract_engine_columns(db, *, now: datetime | None = None) -> ContractSchemaEvolution:
    """Ajoute les colonnes CCNS manquantes après sauvegarde ; idempotent."""
    report = check_schema(db)
    if not report.compatible:
        return ContractSchemaEvolution(False, "Base incompatible : aucune évolution effectuée.")
    missing = report.missing_contract_columns
    if not missing:
        return ContractSchemaEvolution(True, "Colonnes CCNS déjà présentes · aucune écriture.")
    if getattr(db, "isNetwork", False):
        return ContractSchemaEvolution(
            False,
            "Base réseau MySQL : Teamworks Qt ne peut pas la sauvegarder avant l'ajout "
            "des colonnes CCNS. Faites réaliser cet ajout par l'administrateur, ou ouvrez "
            "une fois la page Contrats dans Teamworks (wx).",
        )

    legacy_columns = tuple(
        str(item[0]) for item in db.GetListeChamps2("contrats") if item
    )
    counts_before = _row_counts(db.connexion)
    fingerprint_before = _contracts_fingerprint(db.connexion, legacy_columns)
    backup_path = backup_sqlite(db, now=now)

    types = dict(CONTRACT_ENGINE_COLUMNS)
    created = []
    for name in missing:
        db.AjoutChamp(nomTable="contrats", nomChamp=name, typeChamp=types[name])
        created.append(name)

    after = check_schema(db)
    if after.missing_contract_columns:
        return ContractSchemaEvolution(
            False,
            "Ajout incomplet des colonnes CCNS : %s. Sauvegarde : %s"
            % (", ".join(after.missing_contract_columns), backup_path),
            tuple(created), backup_path,
        )
    if (_row_counts(db.connexion) != counts_before
            or _contracts_fingerprint(db.connexion, legacy_columns) != fingerprint_before):
        return ContractSchemaEvolution(
            False,
            "Contrôle d'intégrité en échec après l'ajout. Restaurez la sauvegarde : %s"
            % backup_path,
            tuple(created), backup_path,
        )
    return ContractSchemaEvolution(
        True,
        "%d colonne(s) CCNS ajoutée(s) · données inchangées · sauvegarde : %s"
        % (len(created), backup_path),
        tuple(created), backup_path,
    )
