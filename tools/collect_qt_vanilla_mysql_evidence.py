#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


SAFE_SUFFIX = "_qt_vanilla_recette"
COUNT_TABLES = (
    "personnes",
    "contrats",
    "presences",
    "scenarios",
    "deplacements",
    "remboursements",
)

MYSQL_VARIABLES = (
    "sql_mode",
    "character_set_server",
    "collation_server",
    "lower_case_table_names",
    "max_allowed_packet",
    "autocommit",
    "tx_isolation",
    "transaction_isolation",
)

PERFORMANCE_THRESHOLDS = {
    "P-01": (3.0, 5.0),
    "P-02": (1.5, 3.0),
    "P-03": (0.5, 1.0),
    "P-04": (1.0, 2.0),
    "P-05": (1.0, 2.0),
    "P-06": (1.5, 3.0),
    "P-07": (1.5, 3.0),
    "P-08": (1.5, 3.0),
    "P-09": (2.0, 3.5),
    "P-10": (2.0, 3.5),
    "P-11": (1.5, 3.0),
}


def _validate_sha(value: str) -> str:
    value = str(value or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Le SHA doit contenir exactement 40 caractères hexadécimaux.")
    return value


def _validate_database(value: str) -> str:
    value = str(value or "").strip()
    if not value.endswith(SAFE_SUFFIX):
        raise ValueError(
            f"La base de recette doit se terminer par {SAFE_SUFFIX!r}."
        )
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError("Nom de base MySQL invalide.")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _nearest_rank(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("Aucune mesure.")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def _median(values: list[float]) -> float:
    if not values:
        raise ValueError("Aucune mesure.")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _mysql_connect(args):
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError(
            "mysql-connector-python est requis pour le relevé MySQL."
        ) from exc

    return mysql.connector.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=os.getenv("TEAMWORKS_MYSQL_PASSWORD", ""),
        database=args.database,
        use_pure=True,
    )


def _fetch_all(cursor, sql: str, params=()) -> list[tuple]:
    cursor.execute(sql, params)
    return list(cursor.fetchall())


def _snapshot(args) -> int:
    database = _validate_database(args.database)
    sha = _validate_sha(args.sha)
    connection = _mysql_connect(args)
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT VERSION()")
        mysql_version = str(cursor.fetchone()[0])

        variables = {}
        cursor.execute("SHOW VARIABLES")
        wanted_variables = {name.lower() for name in MYSQL_VARIABLES}
        for name, value in cursor.fetchall():
            normalized = str(name).lower()
            if normalized in wanted_variables:
                variables[normalized] = str(value)

        tables = [
            {
                "table": str(table),
                "engine": str(engine or ""),
                "collation": str(collation or ""),
            }
            for table, engine, collation in _fetch_all(
                cursor,
                "SELECT table_name, engine, table_collation "
                "FROM information_schema.tables "
                "WHERE table_schema=%s AND table_type='BASE TABLE' "
                "ORDER BY table_name",
                (database,),
            )
        ]

        columns = [
            {
                "table": str(table),
                "column": str(column),
                "type": str(column_type),
                "nullable": str(nullable),
                "default": None if default is None else str(default),
            }
            for table, column, column_type, nullable, default in _fetch_all(
                cursor,
                "SELECT table_name, column_name, column_type, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_schema=%s "
                "ORDER BY table_name, ordinal_position",
                (database,),
            )
        ]

        indexes = [
            {
                "table": str(table),
                "index": str(index),
                "non_unique": int(non_unique),
                "column": str(column),
                "seq": int(seq),
            }
            for table, index, non_unique, column, seq in _fetch_all(
                cursor,
                "SELECT table_name, index_name, non_unique, column_name, seq_in_index "
                "FROM information_schema.statistics "
                "WHERE table_schema=%s "
                "ORDER BY table_name, index_name, seq_in_index",
                (database,),
            )
        ]

        existing_tables = {item["table"] for item in tables}
        counts = {}
        for table in COUNT_TABLES:
            if table not in existing_tables:
                counts[table] = None
                continue
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            counts[table] = int(cursor.fetchone()[0])

        process_rows = []
        try:
            cursor.execute("SHOW PROCESSLIST")
            names = [str(item[0]).lower() for item in cursor.description]
            for row in cursor.fetchall():
                record = dict(zip(names, row))
                if str(record.get("db") or "") != database:
                    continue
                process_rows.append(
                    {
                        "command": str(record.get("command") or ""),
                        "state": str(record.get("state") or ""),
                        "time": int(record.get("time") or 0),
                    }
                )
        except Exception:
            process_rows = []

        process_summary = {
            "count": len(process_rows),
            "commands": dict(Counter(row["command"] for row in process_rows)),
            "states": dict(Counter(row["state"] for row in process_rows)),
            "max_time_seconds": max(
                (row["time"] for row in process_rows),
                default=0,
            ),
        }

        artifacts = []
        for raw_path in args.artifact or ():
            path = Path(raw_path).resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            artifacts.append(
                {
                    "name": path.name,
                    "size": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )

        snapshot = {
            "format": 1,
            "label": args.label,
            "rc_sha": sha,
            "database": database,
            "mysql_version": mysql_version,
            "mysql_variables": variables,
            "schema": {
                "tables": tables,
                "columns": columns,
                "indexes": indexes,
                "tables_hash": _canonical_hash(tables),
                "columns_hash": _canonical_hash(columns),
                "indexes_hash": _canonical_hash(indexes),
            },
            "counts": counts,
            "processlist": process_summary,
            "artifacts": artifacts,
        }

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        return 0
    finally:
        cursor.close()
        connection.close()


def _compare(args) -> int:
    before = json.loads(args.before.read_text(encoding="utf-8"))
    after = json.loads(args.after.read_text(encoding="utf-8"))

    same_sha = before.get("rc_sha") == after.get("rc_sha")
    same_database = before.get("database") == after.get("database")
    same_mysql = before.get("mysql_version") == after.get("mysql_version")

    schema_before = before.get("schema") or {}
    schema_after = after.get("schema") or {}
    schema_equal = {
        "tables": schema_before.get("tables_hash") == schema_after.get("tables_hash"),
        "columns": schema_before.get("columns_hash") == schema_after.get("columns_hash"),
        "indexes": schema_before.get("indexes_hash") == schema_after.get("indexes_hash"),
    }

    count_deltas = {}
    for table in COUNT_TABLES:
        left = (before.get("counts") or {}).get(table)
        right = (after.get("counts") or {}).get(table)
        count_deltas[table] = None if left is None or right is None else right - left

    report = {
        "format": 1,
        "same_sha": same_sha,
        "same_database": same_database,
        "same_mysql_version": same_mysql,
        "schema_equal": schema_equal,
        "count_deltas": count_deltas,
        "processlist_before": (before.get("processlist") or {}).get("count"),
        "processlist_after": (after.get("processlist") or {}).get("count"),
        "automatic_schema_gate": (
            same_sha
            and same_database
            and same_mysql
            and all(schema_equal.values())
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["automatic_schema_gate"] else 2


def _performance(args) -> int:
    grouped: dict[str, list[tuple[float, float | None]]] = {}
    with args.input.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"test_id", "qt_seconds"}
        if not required.issubset(set(reader.fieldnames or ())):
            raise ValueError("CSV attendu : colonnes test_id, qt_seconds, wx_seconds optionnelle.")

        for row in reader:
            test_id = str(row.get("test_id") or "").strip().upper()
            if test_id not in PERFORMANCE_THRESHOLDS:
                raise ValueError(f"Test performance inconnu : {test_id}")
            qt_seconds = float(row["qt_seconds"])
            wx_raw = str(row.get("wx_seconds") or "").strip()
            wx_seconds = float(wx_raw) if wx_raw else None
            if qt_seconds < 0 or (wx_seconds is not None and wx_seconds < 0):
                raise ValueError("Les durées ne peuvent pas être négatives.")
            grouped.setdefault(test_id, []).append((qt_seconds, wx_seconds))

    summary = {}
    global_pass = True
    for test_id, rows in sorted(grouped.items()):
        qt_values = [row[0] for row in rows]
        if len(qt_values) < args.minimum_samples:
            verdict = "NON_QUALIFIE"
            global_pass = False
        else:
            p50 = _median(qt_values)
            p95 = _nearest_rank(qt_values, 0.95)
            p50_limit, p95_limit = PERFORMANCE_THRESHOLDS[test_id]
            verdict = "PASS" if p50 <= p50_limit and p95 <= p95_limit else "FAIL"
            if verdict != "PASS":
                global_pass = False

        p50 = _median(qt_values)
        p95 = _nearest_rank(qt_values, 0.95)
        wx_values = [row[1] for row in rows if row[1] is not None]
        wx_p50 = _median([float(value) for value in wx_values]) if wx_values else None
        ratio = None
        if wx_p50 and wx_p50 > 0:
            ratio = p50 / wx_p50
            if ratio > 1.50:
                verdict = "FAIL"
                global_pass = False
            elif ratio > 1.20 and verdict == "PASS":
                verdict = "ANALYSE"
                global_pass = False

        summary[test_id] = {
            "samples": len(qt_values),
            "p50_seconds": round(p50, 4),
            "p95_seconds": round(p95, 4),
            "p50_limit_seconds": PERFORMANCE_THRESHOLDS[test_id][0],
            "p95_limit_seconds": PERFORMANCE_THRESHOLDS[test_id][1],
            "wx_p50_seconds": None if wx_p50 is None else round(wx_p50, 4),
            "qt_wx_ratio": None if ratio is None else round(ratio, 4),
            "verdict": verdict,
        }

    missing = sorted(set(PERFORMANCE_THRESHOLDS) - set(grouped))
    if missing:
        global_pass = False

    report = {
        "format": 1,
        "minimum_samples": args.minimum_samples,
        "missing_tests": missing,
        "tests": summary,
        "automatic_performance_gate": global_pass and not missing,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["automatic_performance_gate"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collecte des preuves MySQL de la recette Qt Vanilla 0.1."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot = sub.add_parser("snapshot", help="Capture un état MySQL non sensible.")
    snapshot.add_argument("--host", default=os.getenv("TEAMWORKS_MYSQL_HOST", "127.0.0.1"))
    snapshot.add_argument("--port", type=int, default=int(os.getenv("TEAMWORKS_MYSQL_PORT", "3306")))
    snapshot.add_argument("--user", default=os.getenv("TEAMWORKS_MYSQL_USER", "root"))
    snapshot.add_argument("--database", required=True)
    snapshot.add_argument("--sha", required=True)
    snapshot.add_argument("--label", choices=("before", "after", "other"), required=True)
    snapshot.add_argument("--artifact", action="append", default=[])
    snapshot.add_argument("--output", type=Path, required=True)
    snapshot.set_defaults(func=_snapshot)

    compare = sub.add_parser("compare", help="Compare les snapshots avant/après.")
    compare.add_argument("--before", type=Path, required=True)
    compare.add_argument("--after", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    compare.set_defaults(func=_compare)

    perf = sub.add_parser("performance", help="Calcule p50/p95 des mesures P-01 à P-11.")
    perf.add_argument("--input", type=Path, required=True)
    perf.add_argument("--output", type=Path, required=True)
    perf.add_argument("--minimum-samples", type=int, default=10)
    perf.set_defaults(func=_performance)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
