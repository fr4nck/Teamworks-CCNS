#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterable

import mysql.connector

from application.services.representative_copy_anonymization import (
    ANONYMIZED_TEXT,
    assert_safe_recipe_database_name,
    build_sequential_mapping,
    synthetic_birth_date,
    synthetic_identity,
)


SAFE_SUFFIX = "_qt_vanilla_recette"
IDENTITY_DOMAINS = (
    ("personnes", "IDpersonne", ("IDpersonne", "IDindividu"), 100001),
    ("candidats", "IDcandidat", ("IDcandidat",), 200001),
    ("tw_people", "IDtw_person", ("IDtw_person",), 300001),
)

PERSON_DATE_TABLES = {
    "contrats",
    "pieces",
    "presences",
    "scenarios",
    "deplacements",
    "remboursements",
}
TW_DATE_TABLES = {"tw_contracts"}

FREE_TEXT_COLUMNS = {
    "candidatures": (
        "acte_remarques",
        "periodes_remarques",
        "poste_remarques",
        "decision_remarques",
    ),
    "entretiens": ("remarques",),
    "questionnaire_reponses": ("reponse",),
    "contrats_valchamps": ("valeur",),
    "modeles_emails": ("description", "objet", "texte_xml"),
}

BACKUP_TEXT_COLUMNS = (
    "nom",
    "observations",
    "sauvegarde_nom",
    "sauvegarde_motdepasse",
    "sauvegarde_repertoire",
    "sauvegarde_emails",
    "sauvegarde_fichiers_locaux",
    "sauvegarde_fichiers_reseau",
    "condition_jours_scolaires",
    "condition_jours_vacances",
    "condition_heure",
    "condition_poste",
    "condition_derniere",
    "condition_utilisateur",
)

SECRET_COLUMN_MARKERS = (
    "motdepasse",
    "password",
    "passwd",
    "token",
    "secret",
    "apikey",
    "api_key",
)

TEXT_TYPES = {
    "char",
    "varchar",
    "tinytext",
    "text",
    "mediumtext",
    "longtext",
}


def _ident(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", str(name or "")):
        raise ValueError(f"Identifiant SQL refusé : {name!r}")
    return f"`{name}`"


class RecipeDatabase:
    def __init__(self, connection, database: str):
        self.connection = connection
        self.database = database
        self.cursor = connection.cursor()

    def close(self) -> None:
        self.cursor.close()
        self.connection.close()

    def table_exists(self, table: str) -> bool:
        self.cursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema=%s AND table_name=%s",
            (self.database, table),
        )
        return int(self.cursor.fetchone()[0]) > 0

    def columns(self, table: str) -> dict[str, str]:
        self.cursor.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position",
            (self.database, table),
        )
        return {str(name): str(data_type).lower() for name, data_type in self.cursor.fetchall()}

    def tables_with_column(self, column_names: Iterable[str]) -> list[tuple[str, str]]:
        names = tuple(column_names)
        if not names:
            return []
        placeholders = ",".join(["%s"] * len(names))
        self.cursor.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            f"WHERE table_schema=%s AND column_name IN ({placeholders}) "
            "ORDER BY table_name, column_name",
            (self.database, *names),
        )
        return [(str(table), str(column)) for table, column in self.cursor.fetchall()]

    def engines(self) -> dict[str, str]:
        self.cursor.execute(
            "SELECT table_name, COALESCE(engine, '') FROM information_schema.tables "
            "WHERE table_schema=%s AND table_type='BASE TABLE'",
            (self.database,),
        )
        return {str(table): str(engine or "") for table, engine in self.cursor.fetchall()}

    def count(self, table: str) -> int:
        self.cursor.execute(f"SELECT COUNT(*) FROM {_ident(table)}")
        return int(self.cursor.fetchone()[0])

    def scalar(self, sql: str, params=()):
        self.cursor.execute(sql, params)
        row = self.cursor.fetchone()
        return None if row is None else row[0]


def _fetch_ids(db: RecipeDatabase, table: str, column: str) -> list[int]:
    if not db.table_exists(table) or column not in db.columns(table):
        return []
    db.cursor.execute(
        f"SELECT {_ident(column)} FROM {_ident(table)} "
        f"WHERE {_ident(column)} IS NOT NULL AND {_ident(column)} > 0 "
        f"ORDER BY {_ident(column)}"
    )
    return [int(row[0]) for row in db.cursor.fetchall()]


def _case_update(
    db: RecipeDatabase,
    table: str,
    column: str,
    mapping: dict[int, int],
    *,
    chunk_size: int = 200,
) -> None:
    items = list(mapping.items())
    for offset in range(0, len(items), chunk_size):
        chunk = items[offset : offset + chunk_size]
        if not chunk:
            continue
        case_parts = []
        params: list[int] = []
        old_values: list[int] = []
        for old, new in chunk:
            case_parts.append("WHEN %s THEN %s")
            params.extend((old, new))
            old_values.append(old)
        placeholders = ",".join(["%s"] * len(old_values))
        params.extend(old_values)
        db.cursor.execute(
            f"UPDATE {_ident(table)} "
            f"SET {_ident(column)} = CASE {_ident(column)} "
            f"{' '.join(case_parts)} ELSE {_ident(column)} END "
            f"WHERE {_ident(column)} IN ({placeholders})",
            tuple(params),
        )


def _remap_identity_domain(
    db: RecipeDatabase,
    root_table: str,
    root_column: str,
    reference_columns: tuple[str, ...],
    start: int,
) -> dict[int, int]:
    identifiers = _fetch_ids(db, root_table, root_column)
    mapping = build_sequential_mapping(identifiers, start=start)
    if not mapping:
        return {}

    temporary = {old: -new for old, new in mapping.items()}
    references = db.tables_with_column(reference_columns)

    for table, column in references:
        _case_update(db, table, column, temporary)
    reverse = {-new: new for new in mapping.values()}
    for table, column in references:
        _case_update(db, table, column, reverse)
    return mapping


def _anonymize_people(db: RecipeDatabase, mapping: dict[int, int]) -> None:
    if not mapping or not db.table_exists("personnes"):
        return
    cols = db.columns("personnes")
    for sequence, (_old_id, new_id) in enumerate(sorted(mapping.items()), start=1):
        identity = synthetic_identity(sequence)
        birth = None
        if "date_naiss" in cols:
            db.cursor.execute(
                "SELECT date_naiss FROM personnes WHERE IDpersonne=%s",
                (new_id,),
            )
            row = db.cursor.fetchone()
            birth = synthetic_birth_date(row[0] if row else None, sequence)

        assignments = {
            "nom": identity.last_name,
            "nom_jfille": identity.birth_name,
            "prenom": identity.first_name,
            "date_naiss": birth,
            "cp_naiss": identity.postcode,
            "ville_naiss": identity.city,
            "num_secu": "",
            "adresse_resid": identity.address,
            "cp_resid": identity.postcode,
            "ville_resid": identity.city,
            "memo": "",
            "cadre_photo": "",
            "texte_photo": "",
        }
        active = [(name, value) for name, value in assignments.items() if name in cols]
        if active:
            sql = ", ".join(f"{_ident(name)}=%s" for name, _value in active)
            db.cursor.execute(
                f"UPDATE personnes SET {sql} WHERE IDpersonne=%s",
                tuple(value for _name, value in active) + (new_id,),
            )


def _anonymize_candidates(db: RecipeDatabase, mapping: dict[int, int]) -> None:
    if not mapping or not db.table_exists("candidats"):
        return
    cols = db.columns("candidats")
    for sequence, (_old_id, new_id) in enumerate(sorted(mapping.items()), start=1):
        identity = synthetic_identity(sequence + 5000)
        birth = None
        if "date_naiss" in cols:
            db.cursor.execute(
                "SELECT date_naiss FROM candidats WHERE IDcandidat=%s",
                (new_id,),
            )
            row = db.cursor.fetchone()
            birth = synthetic_birth_date(row[0] if row else None, sequence + 5000)

        assignments = {
            "nom": identity.last_name,
            "prenom": identity.first_name,
            "date_naiss": birth,
            "adresse_resid": identity.address,
            "cp_resid": identity.postcode,
            "ville_resid": identity.city,
            "memo": "",
        }
        active = [(name, value) for name, value in assignments.items() if name in cols]
        if active:
            sql = ", ".join(f"{_ident(name)}=%s" for name, _value in active)
            db.cursor.execute(
                f"UPDATE candidats SET {sql} WHERE IDcandidat=%s",
                tuple(value for _name, value in active) + (new_id,),
            )


def _anonymize_tw_people(db: RecipeDatabase, mapping: dict[int, int]) -> None:
    if not mapping or not db.table_exists("tw_people"):
        return
    cols = db.columns("tw_people")
    for sequence, (_old_id, new_id) in enumerate(sorted(mapping.items()), start=1):
        identity = synthetic_identity(sequence + 9000)
        birth = None
        if "date_naissance" in cols:
            db.cursor.execute(
                "SELECT date_naissance FROM tw_people WHERE IDtw_person=%s",
                (new_id,),
            )
            row = db.cursor.fetchone()
            birth = synthetic_birth_date(row[0] if row else None, sequence + 9000)
        assignments = {
            "code_interne": f"TW-REC-{sequence:05d}",
            "nom_affiche": f"{identity.first_name} {identity.last_name}",
            "date_naissance": birth,
        }
        active = [(name, value) for name, value in assignments.items() if name in cols]
        if active:
            sql = ", ".join(f"{_ident(name)}=%s" for name, _value in active)
            db.cursor.execute(
                f"UPDATE tw_people SET {sql} WHERE IDtw_person=%s",
                tuple(value for _name, value in active) + (new_id,),
            )


def _anonymize_contacts(db: RecipeDatabase) -> None:
    if db.table_exists("coordonnees"):
        cols = db.columns("coordonnees")
        if {"IDpersonne", "categorie", "texte"}.issubset(cols):
            intitule = ", intitule='Coordonnée de recette'" if "intitule" in cols else ""
            db.cursor.execute(
                "UPDATE coordonnees SET texte = CASE "
                "WHEN LOWER(categorie) LIKE '%mail%' "
                "THEN CONCAT('personne_', LPAD(IDpersonne, 6, '0'), '@example.test') "
                "WHEN LOWER(categorie) LIKE '%mobile%' OR LOWER(categorie) LIKE '%fixe%' "
                "OR LOWER(categorie) LIKE '%tel%' "
                "THEN CONCAT('00000', LPAD(MOD(IDpersonne, 100000), 5, '0')) "
                f"ELSE '{ANONYMIZED_TEXT}' END{intitule}"
            )
    if db.table_exists("coords_candidats"):
        cols = db.columns("coords_candidats")
        if {"IDcandidat", "categorie", "texte"}.issubset(cols):
            intitule = ", intitule='Coordonnée de recette'" if "intitule" in cols else ""
            db.cursor.execute(
                "UPDATE coords_candidats SET texte = CASE "
                "WHEN LOWER(categorie) LIKE '%mail%' "
                "THEN CONCAT('candidat_', LPAD(IDcandidat, 6, '0'), '@example.test') "
                "WHEN LOWER(categorie) LIKE '%mobile%' OR LOWER(categorie) LIKE '%fixe%' "
                "OR LOWER(categorie) LIKE '%tel%' "
                "THEN CONCAT('00000', LPAD(MOD(IDcandidat, 100000), 5, '0')) "
                f"ELSE '{ANONYMIZED_TEXT}' END{intitule}"
            )


def _shift_person_dates(db: RecipeDatabase, mapping: dict[int, int]) -> None:
    if not mapping:
        return
    for table in sorted(PERSON_DATE_TABLES):
        if not db.table_exists(table):
            continue
        cols = db.columns(table)
        if "IDpersonne" not in cols:
            continue
        date_columns = [
            name
            for name, data_type in cols.items()
            if data_type in {"date", "datetime", "timestamp"}
            and (name == "date" or name.startswith("date_"))
        ]
        for sequence, (_old_id, new_id) in enumerate(sorted(mapping.items()), start=1):
            shift = synthetic_identity(sequence).date_shift_days
            for column in date_columns:
                db.cursor.execute(
                    f"UPDATE {_ident(table)} "
                    f"SET {_ident(column)}=DATE_ADD({_ident(column)}, INTERVAL %s DAY) "
                    f"WHERE IDpersonne=%s AND {_ident(column)} IS NOT NULL",
                    (shift, new_id),
                )


def _shift_tw_dates(db: RecipeDatabase, mapping: dict[int, int]) -> None:
    if not mapping:
        return
    for table in sorted(TW_DATE_TABLES):
        if not db.table_exists(table):
            continue
        cols = db.columns(table)
        if "IDtw_person" not in cols:
            continue
        date_columns = [
            name
            for name, data_type in cols.items()
            if data_type in {"date", "datetime", "timestamp"}
            and (name == "date" or name.startswith("date_"))
        ]
        for sequence, (_old_id, new_id) in enumerate(sorted(mapping.items()), start=1):
            shift = synthetic_identity(sequence + 9000).date_shift_days
            for column in date_columns:
                db.cursor.execute(
                    f"UPDATE {_ident(table)} "
                    f"SET {_ident(column)}=DATE_ADD({_ident(column)}, INTERVAL %s DAY) "
                    f"WHERE IDtw_person=%s AND {_ident(column)} IS NOT NULL",
                    (shift, new_id),
                )


def _anonymize_free_text(db: RecipeDatabase) -> None:
    for table, names in FREE_TEXT_COLUMNS.items():
        if not db.table_exists(table):
            continue
        cols = db.columns(table)
        for name in names:
            if name not in cols:
                continue
            db.cursor.execute(
                f"UPDATE {_ident(table)} SET {_ident(name)}=%s "
                f"WHERE {_ident(name)} IS NOT NULL AND TRIM(CAST({_ident(name)} AS CHAR)) <> ''",
                (ANONYMIZED_TEXT,),
            )

    if db.table_exists("presences") and "intitule" in db.columns("presences"):
        db.cursor.execute(
            "UPDATE presences SET intitule='Présence de recette' "
            "WHERE intitule IS NOT NULL AND TRIM(intitule)<>''"
        )
    if db.table_exists("scenarios"):
        cols = db.columns("scenarios")
        if "nom" in cols:
            db.cursor.execute(
                "UPDATE scenarios SET nom=CONCAT('Scénario recette ', IDscenario)"
            )
        if "description" in cols:
            db.cursor.execute(
                "UPDATE scenarios SET description=%s "
                "WHERE description IS NOT NULL AND TRIM(description)<>''",
                (ANONYMIZED_TEXT,),
            )
    if db.table_exists("deplacements"):
        cols = db.columns("deplacements")
        assignments = []
        if "objet" in cols:
            assignments.append("objet='Déplacement de recette'")
        if "cp_depart" in cols:
            assignments.append("cp_depart='90001'")
        if "ville_depart" in cols:
            assignments.append("ville_depart='Ville-Départ-Recette'")
        if "cp_arrivee" in cols:
            assignments.append("cp_arrivee='90002'")
        if "ville_arrivee" in cols:
            assignments.append("ville_arrivee='Ville-Arrivée-Recette'")
        if assignments:
            db.cursor.execute("UPDATE deplacements SET " + ", ".join(assignments))


def _sanitize_mail_and_settings(db: RecipeDatabase) -> None:
    if db.table_exists("adresses_mail"):
        cols = db.columns("adresses_mail")
        assignments = {
            "adresse": "noreply@example.test",
            "nom_adresse": "Adresse de recette",
            "motdepasse": "",
            "smtp": "smtp.example.test",
            "utilisateur": "",
            "parametres": "",
        }
        active = [(name, value) for name, value in assignments.items() if name in cols]
        if active:
            sql = ", ".join(f"{_ident(name)}=%s" for name, _value in active)
            db.cursor.execute(
                f"UPDATE adresses_mail SET {sql}",
                tuple(value for _name, value in active),
            )

    if db.table_exists("profils_parametres") and "parametre" in db.columns("profils_parametres"):
        db.cursor.execute("UPDATE profils_parametres SET parametre=''")

    if db.table_exists("sauvegardes_auto"):
        cols = db.columns("sauvegardes_auto")
        active = [name for name in BACKUP_TEXT_COLUMNS if name in cols]
        if active:
            db.cursor.execute(
                "UPDATE sauvegardes_auto SET "
                + ", ".join(f"{_ident(name)}=''" for name in active)
            )

    # Toute colonne dont le nom signale explicitement un secret est vidée,
    # y compris dans les tables ajoutées après ce script.
    db.cursor.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=%s ORDER BY table_name, ordinal_position",
        (db.database,),
    )
    for table, column, data_type in db.cursor.fetchall():
        lower = str(column).lower()
        if str(data_type).lower() not in TEXT_TYPES:
            continue
        if not any(marker in lower for marker in SECRET_COLUMN_MARKERS):
            continue
        db.cursor.execute(
            f"UPDATE {_ident(str(table))} SET {_ident(str(column))}=''"
        )


def _sanitize_salary_fields(
    db: RecipeDatabase,
    person_mapping: dict[int, int],
    tw_mapping: dict[int, int],
) -> None:
    if db.table_exists("contrats") and person_mapping:
        cols = db.columns("contrats")
        salary_columns = [
            name
            for name in cols
            if "salaire" in name.lower() or "remuner" in name.lower()
        ]
        for sequence, (_old_id, new_id) in enumerate(sorted(person_mapping.items()), start=1):
            monthly = 1800 + (sequence % 7) * 150
            for column in salary_columns:
                value = monthly * 12 if "ann" in column.lower() else monthly
                db.cursor.execute(
                    f"UPDATE contrats SET {_ident(column)}=%s WHERE IDpersonne=%s",
                    (value, new_id),
                )

    if db.table_exists("tw_contracts") and tw_mapping:
        cols = db.columns("tw_contracts")
        salary_columns = [
            name
            for name in cols
            if "salaire" in name.lower() or "remuner" in name.lower()
        ]
        for sequence, (_old_id, new_id) in enumerate(sorted(tw_mapping.items()), start=1):
            monthly = 1800 + (sequence % 7) * 150
            for column in salary_columns:
                value = monthly * 12 if "ann" in column.lower() else monthly
                db.cursor.execute(
                    f"UPDATE tw_contracts SET {_ident(column)}=%s WHERE IDtw_person=%s",
                    (value, new_id),
                )


def _delete_sensitive_blobs(db: RecipeDatabase) -> dict[str, int]:
    deleted = {}
    for table in ("photos", "documents"):
        if not db.table_exists(table):
            continue
        before = db.count(table)
        db.cursor.execute(f"DELETE FROM {_ident(table)}")
        deleted[table] = before
    return deleted


def audit_anonymized_copy(db: RecipeDatabase) -> list[str]:
    issues: list[str] = []

    for table in ("photos", "documents"):
        if db.table_exists(table) and db.count(table):
            issues.append(f"{table}: des BLOBs sensibles subsistent")

    if db.table_exists("personnes"):
        cols = db.columns("personnes")
        for name in ("num_secu", "memo", "cadre_photo", "texte_photo"):
            if name in cols:
                count = int(
                    db.scalar(
                        f"SELECT COUNT(*) FROM personnes "
                        f"WHERE {_ident(name)} IS NOT NULL "
                        f"AND TRIM(CAST({_ident(name)} AS CHAR))<>''"
                    )
                    or 0
                )
                if count:
                    issues.append(f"personnes.{name}: {count} valeurs non neutralisées")

    if db.table_exists("candidats") and "memo" in db.columns("candidats"):
        count = int(
            db.scalar(
                "SELECT COUNT(*) FROM candidats "
                "WHERE memo IS NOT NULL AND TRIM(memo)<>''"
            )
            or 0
        )
        if count:
            issues.append(f"candidats.memo: {count} valeurs non neutralisées")

    # Secrets nommés explicitement.
    db.cursor.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=%s ORDER BY table_name, ordinal_position",
        (db.database,),
    )
    for table, column, data_type in db.cursor.fetchall():
        lower = str(column).lower()
        if str(data_type).lower() not in TEXT_TYPES:
            continue
        if not any(marker in lower for marker in SECRET_COLUMN_MARKERS):
            continue
        count = int(
            db.scalar(
                f"SELECT COUNT(*) FROM {_ident(str(table))} "
                f"WHERE {_ident(str(column))} IS NOT NULL "
                f"AND TRIM(CAST({_ident(str(column))} AS CHAR))<>''"
            )
            or 0
        )
        if count:
            issues.append(f"{table}.{column}: {count} secrets potentiels")

    # Toute adresse mail restante doit utiliser le domaine réservé example.test.
    db.cursor.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=%s ORDER BY table_name, ordinal_position",
        (db.database,),
    )
    for table, column, data_type in db.cursor.fetchall():
        if str(data_type).lower() not in TEXT_TYPES:
            continue
        count = int(
            db.scalar(
                f"SELECT COUNT(*) FROM {_ident(str(table))} "
                f"WHERE CAST({_ident(str(column))} AS CHAR) LIKE '%@%' "
                f"AND CAST({_ident(str(column))} AS CHAR) NOT LIKE '%@example.test%'"
            )
            or 0
        )
        if count:
            issues.append(f"{table}.{column}: {count} adresses mail non synthétiques")

    return issues


def anonymize(db: RecipeDatabase) -> dict[str, object]:
    engines = db.engines()
    non_transactional = sorted(
        table for table, engine in engines.items()
        if engine and engine.lower() not in {"innodb"}
    )

    mappings: dict[str, dict[int, int]] = {}
    for root_table, root_column, references, start in IDENTITY_DOMAINS:
        mappings[root_table] = _remap_identity_domain(
            db, root_table, root_column, references, start
        )

    people = mappings.get("personnes", {})
    candidates = mappings.get("candidats", {})
    tw_people = mappings.get("tw_people", {})

    _anonymize_people(db, people)
    _anonymize_candidates(db, candidates)
    _anonymize_tw_people(db, tw_people)
    _anonymize_contacts(db)
    _shift_person_dates(db, people)
    _shift_tw_dates(db, tw_people)
    _sanitize_salary_fields(db, people, tw_people)
    _anonymize_free_text(db)
    _sanitize_mail_and_settings(db)
    deleted_blobs = _delete_sensitive_blobs(db)

    issues = audit_anonymized_copy(db)
    return {
        "database": db.database,
        "persons": len(people),
        "candidates": len(candidates),
        "tw_people": len(tw_people),
        "deleted_blobs": deleted_blobs,
        "non_transactional_tables": non_transactional,
        "audit_issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Anonymise une COPIE MySQL dédiée à la recette Qt Vanilla 0.1."
    )
    parser.add_argument("--host", default=os.getenv("TEAMWORKS_MYSQL_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("TEAMWORKS_MYSQL_PORT", "3306")))
    parser.add_argument("--user", default=os.getenv("TEAMWORKS_MYSQL_USER", "root"))
    parser.add_argument("--database", required=True)
    parser.add_argument("--confirm-database", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Applique les modifications. Sans ce flag, aucun UPDATE/DELETE n'est exécuté.",
    )
    parser.add_argument(
        "--acknowledge-nontransactional",
        action="store_true",
        help="Autorise une copie contenant des tables non-InnoDB. À utiliser uniquement sur une copie jetable.",
    )
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    assert_safe_recipe_database_name(args.database, args.confirm_database)

    password = os.getenv("TEAMWORKS_MYSQL_PASSWORD", "")
    connection = mysql.connector.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        database=args.database,
        use_pure=True,
    )
    connection.autocommit = False
    db = RecipeDatabase(connection, args.database)

    try:
        engines = db.engines()
        non_transactional = sorted(
            table for table, engine in engines.items()
            if engine and engine.lower() not in {"innodb"}
        )
        overview = {
            "database": args.database,
            "mode": "apply" if args.apply else "dry-run",
            "tables": len(engines),
            "non_transactional_tables": non_transactional,
            "personnes": db.count("personnes") if db.table_exists("personnes") else 0,
            "candidats": db.count("candidats") if db.table_exists("candidats") else 0,
        }

        if not args.apply:
            report = overview
        else:
            if non_transactional and not args.acknowledge_nontransactional:
                names = ", ".join(non_transactional[:12])
                raise RuntimeError(
                    "La copie contient des tables non transactionnelles "
                    f"({names}). Recréer une copie jetable puis relancer avec "
                    "--acknowledge-nontransactional si ce risque est accepté."
                )

            db.cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            report = anonymize(db)
            if report["audit_issues"]:
                connection.rollback()
                raise RuntimeError(
                    "Audit d'anonymisation en échec : "
                    + "; ".join(report["audit_issues"])
                )
            connection.commit()

        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    finally:
        try:
            db.cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        except Exception:
            pass
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
