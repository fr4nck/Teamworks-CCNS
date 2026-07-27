#!/usr/bin/env python3
"""Recette fonctionnelle transactionnelle sur une copie des bases d'exemple.

Ce test ne touche jamais aux fichiers fournis avec Teamworks. Il copie les trois
bases Exemple dans un répertoire temporaire, exerce les opérations CRUD
principales sur TDATA, crée une sauvegarde, puis contrôle l'intégrité SQLite.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "teamworks" / "Static" / "Exemples"
SUFFIXES = ("TDATA", "TDOCUMENTS", "TPHOTOS")


def copy_example_set(target_dir: Path) -> dict[str, Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, Path] = {}
    for suffix in SUFFIXES:
        source = EXAMPLE_DIR / f"Exemple_{suffix}.dat"
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = target_dir / source.name
        shutil.copy2(source, destination)
        copied[suffix] = destination
    return copied


def integrity_check(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def exercise_tdata(path: Path) -> dict[str, int | str]:
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        before = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("personnes", "presences", "contrats")
        }

        cursor = connection.execute(
            """
            INSERT INTO personnes (
                civilite, nom, prenom, date_naiss, adresse_resid,
                cp_resid, ville_resid, memo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "M.",
                "RECETTE",
                "Fonctionnelle",
                "1990-01-01",
                "1 rue du Test",
                35000,
                "Rennes",
                "Créé automatiquement sur une copie temporaire",
            ),
        )
        person_id = int(cursor.lastrowid)

        connection.execute(
            "UPDATE personnes SET memo = ? WHERE IDpersonne = ?",
            ("Modification validée", person_id),
        )
        updated_memo = connection.execute(
            "SELECT memo FROM personnes WHERE IDpersonne = ?", (person_id,)
        ).fetchone()
        if updated_memo != ("Modification validée",):
            raise AssertionError("La modification de la personne n'a pas été persistée")

        category_row = connection.execute(
            "SELECT IDcategorie FROM cat_presences ORDER BY IDcategorie LIMIT 1"
        ).fetchone()
        category_id = int(category_row[0]) if category_row else None
        presence_cursor = connection.execute(
            """
            INSERT INTO presences (
                IDpersonne, date, heure_debut, heure_fin, IDcategorie, intitule
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (person_id, "2026-07-26", "09:00", "12:00", category_id, "Recette automatisée"),
        )
        presence_id = int(presence_cursor.lastrowid)

        type_row = connection.execute(
            "SELECT IDtype FROM contrats_types ORDER BY IDtype LIMIT 1"
        ).fetchone()
        class_row = connection.execute(
            "SELECT IDclassification FROM contrats_class ORDER BY IDclassification LIMIT 1"
        ).fetchone()
        contract_cursor = connection.execute(
            """
            INSERT INTO contrats (
                IDpersonne, IDclassification, IDtype, date_debut,
                essai, signature, due
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                int(class_row[0]) if class_row else None,
                int(type_row[0]) if type_row else None,
                "2026-07-26",
                0,
                "oui",
                "oui",
            ),
        )
        contract_id = int(contract_cursor.lastrowid)
        connection.commit()

        linked = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM presences WHERE IDpresence = ? AND IDpersonne = ?),
                (SELECT COUNT(*) FROM contrats WHERE IDcontrat = ? AND IDpersonne = ?)
            """,
            (presence_id, person_id, contract_id, person_id),
        ).fetchone()
        if linked != (1, 1):
            raise AssertionError("Les enregistrements secondaires ne sont pas reliés à la personne")

        connection.execute("DELETE FROM presences WHERE IDpresence = ?", (presence_id,))
        connection.execute("DELETE FROM contrats WHERE IDcontrat = ?", (contract_id,))
        connection.execute("DELETE FROM personnes WHERE IDpersonne = ?", (person_id,))
        connection.commit()

        after = {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("personnes", "presences", "contrats")
        }
        if before != after:
            raise AssertionError(f"Le nettoyage final est incomplet: avant={before}, après={after}")

    return {
        "person_id": person_id,
        "presence_id": presence_id,
        "contract_id": contract_id,
        "integrity": integrity_check(path),
    }


def run(output_dir: Path | None = None) -> dict[str, object]:
    if output_dir is None:
        temp_context = tempfile.TemporaryDirectory(prefix="teamworks-functional-")
        workdir = Path(temp_context.name)
    else:
        temp_context = None
        workdir = output_dir

    try:
        databases = copy_example_set(workdir)
        initial_integrity = {suffix: integrity_check(path) for suffix, path in databases.items()}
        if set(initial_integrity.values()) != {"ok"}:
            raise AssertionError(f"Intégrité initiale invalide: {initial_integrity}")

        roundtrip = exercise_tdata(databases["TDATA"])
        backup = workdir / "Sauvegarde_Exemple_TDATA.dat"
        shutil.copy2(databases["TDATA"], backup)
        backup_integrity = integrity_check(backup)
        if backup_integrity != "ok":
            raise AssertionError(f"Sauvegarde SQLite invalide: {backup_integrity}")

        final_integrity = {suffix: integrity_check(path) for suffix, path in databases.items()}
        return {
            "status": "ok",
            "workdir": str(workdir),
            "initial_integrity": initial_integrity,
            "roundtrip": roundtrip,
            "final_integrity": final_integrity,
            "backup_integrity": backup_integrity,
        }
    finally:
        if temp_context is not None:
            temp_context.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run(args.output_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("TEAMWORKS_FUNCTIONAL_DB_ROUNDTRIP_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
