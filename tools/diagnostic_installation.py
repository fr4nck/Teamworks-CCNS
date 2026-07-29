#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostic reproductible d'une installation Teamworks-CCNS.

Le script ne modifie pas les données métier. Il vérifie les ressources minimales,
la possibilité d'écrire dans le dossier utilisateur et, sur demande, la lisibilité
d'une base SQLite ouverte strictement en lecture seule.
"""

from __future__ import annotations

import argparse
import os
import platform
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


REQUIRED_RESOURCES = (
    "teamworks/Static/Images/16x16/Logo.png",
    "teamworks/Static/Images/32x32/Maison.png",
    "teamworks/FonctionsPerso.py",
    "teamworks/GestionDB.py",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str

    def render(self) -> str:
        status = "OK" if self.ok else "ERREUR"
        return f"[{status}] {self.name}: {self.detail}"


def resolve_user_directory() -> Path:
    """Retourne le dossier utilisateur sans dépendre de wxPython."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "Teamworks-CCNS"
    return Path.home() / ".teamworks-ccns"


def check_resources(root: Path) -> list[CheckResult]:
    results = []
    for relative_path in REQUIRED_RESOURCES:
        absolute_path = root / relative_path
        results.append(
            CheckResult(
                name=f"Ressource {relative_path}",
                ok=absolute_path.is_file(),
                detail=str(absolute_path),
            )
        )
    return results


def check_user_directory(path: Path) -> CheckResult:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix="tw-diagnostic-", dir=path, delete=True) as handle:
            handle.write(b"ok")
            handle.flush()
        return CheckResult("Dossier utilisateur", True, f"écriture possible dans {path}")
    except OSError as exc:
        return CheckResult("Dossier utilisateur", False, f"écriture impossible dans {path}: {exc}")


def check_database(path: Path) -> CheckResult:
    """Contrôle une base SQLite sans autoriser aucune création ni écriture."""
    database_path = path.expanduser().resolve()
    if not database_path.is_file():
        return CheckResult("Base SQLite", False, f"fichier introuvable: {database_path}")

    uri = f"{database_path.as_uri()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=2.0) as connection:
            integrity = connection.execute("PRAGMA quick_check").fetchone()
            if not integrity or integrity[0] != "ok":
                detail = integrity[0] if integrity else "résultat absent"
                return CheckResult("Base SQLite", False, f"quick_check: {detail}")
            table_count = connection.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
            ).fetchone()[0]
    except sqlite3.Error as exc:
        return CheckResult("Base SQLite", False, f"ouverture en lecture seule impossible: {exc}")

    return CheckResult(
        "Base SQLite",
        True,
        f"lecture seule OK, intégrité OK, {table_count} table(s): {database_path}",
    )


def build_report(
    root: Path,
    user_directory: Path | None = None,
    database: Path | None = None,
) -> tuple[str, bool]:
    user_directory = user_directory or resolve_user_directory()
    checks: list[CheckResult] = []
    checks.extend(check_resources(root))
    checks.append(check_user_directory(user_directory))
    if database is not None:
        checks.append(check_database(database))

    lines = [
        "Diagnostic d'installation Teamworks-CCNS",
        f"Date: {datetime.now().isoformat(timespec='seconds')}",
        f"Python: {platform.python_version()}",
        f"Système: {platform.platform()}",
        f"Architecture: {platform.machine()}",
        f"Racine contrôlée: {root}",
        f"Dossier utilisateur: {user_directory}",
        f"Base contrôlée: {database.expanduser().resolve() if database else 'non demandée'}",
        "",
    ]
    lines.extend(result.render() for result in checks)
    success = all(result.ok for result in checks)
    lines.extend(("", f"Résultat global: {'OK' if success else 'ERREUR'}"))
    return "\n".join(lines) + "\n", success


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Racine du dépôt ou du paquet portable à contrôler.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        help="Base SQLite à contrôler strictement en lecture seule.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Fichier de rapport. Par défaut, affichage dans la console.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    report, success = build_report(
        args.root.resolve(),
        database=args.database,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
