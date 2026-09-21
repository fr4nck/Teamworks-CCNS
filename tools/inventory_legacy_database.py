#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventaire d'une base historique Noethys/Teamworks, avant toute migration.

Ouvre une copie/snapshot de la base en lecture seule, mesure ce qu'elle
contient réellement (tables, colonnes, NULL, doublons, orphelins, ...),
puis, si les tables du pilote Frais sont présentes, exécute l'analyse
spécialisée de domain/migration/expense_inventory.py.

Ne modifie jamais la base source. Ne migre rien. Produit un JSON
machine-readable et/ou un Markdown humain.

Exemples :

    python tools/inventory_legacy_database.py --sqlite copie_noethys.sqlite \\
        --json artifacts/inventaire.json --markdown artifacts/inventaire.md

    python tools/inventory_legacy_database.py \\
        --mysql-host db.example.org --mysql-user lecture --mysql-database noethys \\
        --mysql-password-env TEAMWORKS_MYSQL_PASSWORD \\
        --json artifacts/inventaire.json --markdown artifacts/inventaire.md

Le mot de passe MySQL n'est jamais passé en argument : il est lu dans la
variable d'environnement désignée par --mysql-password-env, pour ne
jamais finir dans l'historique shell ou les journaux de lancement.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain.migration.expense_inventory import analyze_expense_pilot_source
from domain.migration.expense_inventory_loader import (
    load_expense_pilot_person_ids,
    load_expense_pilot_reimbursements,
    load_expense_pilot_trips,
)
from domain.migration.inventory_engine import build_database_inventory
from domain.migration.migration_report import (
    build_migration_inventory_report,
    render_markdown,
    to_json_dict,
)

FRAIS_REQUIRED_TABLES = ("personnes", "deplacements", "remboursements")


class InventoryToolError(Exception):
    """Erreur technique de l'outil (connexion, fichier, arguments)."""


def _open_sqlite_port(path: str):
    from infrastructure.persistence.legacy_sqlite_inventory_adapter import (
        SqliteLegacyDatabasePort,
    )

    try:
        return SqliteLegacyDatabasePort.from_path(path)
    except FileNotFoundError as exc:
        raise InventoryToolError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - défensif, erreurs sqlite3 variées
        raise InventoryToolError(f"Impossible d'ouvrir la base SQLite : {exc}") from exc


def _open_mysql_port(args: argparse.Namespace):
    from infrastructure.persistence.legacy_mysql_inventory_adapter import (
        MySqlLegacyDatabasePort,
        connect_mysql,
    )

    password = os.environ.get(args.mysql_password_env)
    if password is None:
        raise InventoryToolError(
            f"Variable d'environnement {args.mysql_password_env!r} absente : "
            "le mot de passe MySQL ne peut pas être lu."
        )
    try:
        connection = connect_mysql(
            host=args.mysql_host,
            port=args.mysql_port,
            user=args.mysql_user,
            password=password,
            database=args.mysql_database,
        )
    except Exception as exc:
        raise InventoryToolError(f"Connexion MySQL impossible : {exc}") from exc
    return MySqlLegacyDatabasePort(
        connection,
        database=args.mysql_database,
        source_label=f"mysql://{args.mysql_user}@{args.mysql_host}/{args.mysql_database}",
    )


def build_report(port, *, sample_limit: int, skip_frais: bool):
    database = build_database_inventory(port, sample_limit=sample_limit)

    expense = None
    if not skip_frais:
        available_tables = {t.name for t in database.tables}
        if all(name in available_tables for name in FRAIS_REQUIRED_TABLES):
            expense = analyze_expense_pilot_source(
                source_people_ids=load_expense_pilot_person_ids(port),
                trips=load_expense_pilot_trips(port),
                reimbursements=load_expense_pilot_reimbursements(port),
            )

    return build_migration_inventory_report(database, expense=expense)


def _write_outputs(report, *, json_path: str | None, markdown_path: str | None) -> None:
    payload = to_json_dict(report)
    if json_path:
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(json_path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if markdown_path:
        Path(markdown_path).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown_path).write_text(render_markdown(report), encoding="utf-8")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sqlite", metavar="PATH", help="Chemin d'une copie SQLite en lecture seule.")
    source.add_argument(
        "--mysql-host", metavar="HOST", help="Hôte MySQL (implique --mysql-user/--mysql-database)."
    )

    parser.add_argument("--mysql-port", type=int, default=3306)
    parser.add_argument("--mysql-user", metavar="USER")
    parser.add_argument("--mysql-database", metavar="DB")
    parser.add_argument(
        "--mysql-password-env",
        metavar="VARNAME",
        default="TEAMWORKS_MYSQL_PASSWORD",
        help="Nom de la variable d'environnement contenant le mot de passe MySQL.",
    )

    parser.add_argument("--json", dest="json_path", metavar="PATH", help="Chemin de sortie JSON.")
    parser.add_argument("--markdown", dest="markdown_path", metavar="PATH", help="Chemin de sortie Markdown.")
    parser.add_argument("--sample-limit", type=int, default=3, help="Nombre d'exemples de valeurs par colonne.")
    parser.add_argument(
        "--no-frais",
        action="store_true",
        help="Désactive l'analyse spécialisée du pilote Frais même si les tables sont présentes.",
    )

    args = parser.parse_args(argv)

    if args.mysql_host and (not args.mysql_user or not args.mysql_database):
        parser.error("--mysql-host requiert --mysql-user et --mysql-database")

    try:
        if args.sqlite:
            port = _open_sqlite_port(args.sqlite)
        else:
            port = _open_mysql_port(args)

        try:
            report = build_report(port, sample_limit=args.sample_limit, skip_frais=args.no_frais)
        finally:
            port.close()
    except InventoryToolError as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 1

    _write_outputs(report, json_path=args.json_path, markdown_path=args.markdown_path)

    print(
        json.dumps(
            {
                "source_label": report.database.source_label,
                "engine": report.database.engine,
                "table_count": report.database.table_count,
                "total_row_count": report.database.total_row_count,
                "blocking_findings": len(report.blocking_findings),
                "review_findings": len(report.review_findings),
                "info_findings": len(report.info_findings),
                "decision": report.decision,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
