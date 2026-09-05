#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""CLI de migration des rattachements remboursements / déplacements."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

RACINE_DEPOT = Path(__file__).resolve().parents[1]
if str(RACINE_DEPOT) not in sys.path:
    sys.path.insert(0, str(RACINE_DEPOT))

from teamworks.CcnsCore.migration_remboursements_deplacements import (
    MigrationBloquee,
    RollbackRefuse,
    SnapshotInvalide,
    appliquer_base_sqlite,
    planifier_base_sqlite,
    restaurer_snapshot_sqlite,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Réconcilier les rattachements remboursements/déplacements en faisant "
            "de deplacements.IDremboursement la source canonique."
        )
    )
    sous = parser.add_subparsers(dest="commande", required=True)

    plan = sous.add_parser("plan", help="dry-run strictement en lecture seule")
    plan.add_argument("base", help="fichier SQLite Teamworks existant")
    plan.add_argument(
        "--recuperer-parent-unique",
        action="store_true",
        help=(
            "proposer la récupération d'un enfant libre lorsqu'une seule projection "
            "parent de la même personne le revendique"
        ),
    )

    appliquer = sous.add_parser(
        "apply",
        help="appliquer le plan dans une transaction unique après snapshot",
    )
    appliquer.add_argument("base", help="fichier SQLite Teamworks existant")
    appliquer.add_argument(
        "--recuperer-parent-unique",
        action="store_true",
        help=(
            "récupérer les revendications parent uniques et non ambiguës ; sans cette "
            "option la clé enfant libre gagne"
        ),
    )
    appliquer.add_argument(
        "--snapshot",
        help="chemin du snapshot externe ; doit ne pas exister",
    )

    rollback = sous.add_parser(
        "rollback",
        help="restaurer exactement les deux représentations depuis un snapshot",
    )
    rollback.add_argument("base", help="fichier SQLite Teamworks existant")
    rollback.add_argument("snapshot", help="snapshot créé par la commande apply")
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.commande == "plan":
            plan = planifier_base_sqlite(
                args.base,
                recuperer_parent_unique=args.recuperer_parent_unique,
            )
            print(plan.render_text())
            return 0 if plan.applicable else 2

        if args.commande == "apply":
            resultat = appliquer_base_sqlite(
                args.base,
                recuperer_parent_unique=args.recuperer_parent_unique,
                chemin_snapshot=args.snapshot,
            )
            print(resultat.plan.render_text())
            print("\nMigration validée et commitée atomiquement.")
            print("Snapshot : %s" % resultat.snapshot)
            print("État après SHA-256 : %s" % resultat.etat_apres_sha256)
            return 0

        resultat = restaurer_snapshot_sqlite(args.base, args.snapshot)
        print("Rollback validé et commité atomiquement.")
        print("Snapshot : %s" % resultat.snapshot)
        print("État restauré SHA-256 : %s" % resultat.etat_restaure_sha256)
        return 0
    except MigrationBloquee as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (SnapshotInvalide, RollbackRefuse) as exc:
        print("Erreur de sécurité : %s" % exc, file=sys.stderr)
        return 3
    except (OSError, sqlite3.Error) as exc:
        print("Erreur d'accès : %s" % exc, file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
