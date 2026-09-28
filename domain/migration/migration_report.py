"""Rapport d'inventaire de migration : agrégation, décision, rendu JSON/Markdown.

Ce module ne modifie ni ne masque aucune anomalie : il se contente de les
regrouper et d'appliquer la règle de décision automatique documentée dans
docs/66-strategie-migration-noethys-teamworks.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from domain.migration.expense_inventory import ExpenseInventoryResult
from domain.migration.finding import Finding
from domain.migration.inventory_model import ColumnStats, DatabaseInventory, TableInventory
from domain.migration.severity import Severity

READY_FOR_MIGRATION_ANALYSIS = "READY_FOR_MIGRATION_ANALYSIS"
REVIEW_REQUIRED = "REVIEW_REQUIRED"


def _generic_findings(database: DatabaseInventory) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for table in database.tables:
        if not table.primary_key_columns:
            findings.append(
                Finding(
                    code="TABLE_PRIMARY_KEY_UNKNOWN",
                    severity=Severity.REVIEW,
                    table=table.name,
                    row_id="*",
                    message="Aucune clé primaire détectée pour cette table.",
                )
            )
            continue
        if table.duplicate_key_row_count:
            findings.append(
                Finding(
                    code="TABLE_PRIMARY_KEY_DUPLICATED",
                    severity=Severity.BLOCKING,
                    table=table.name,
                    row_id="*",
                    message=(
                        f"{table.duplicate_key_row_count} ligne(s) en surnombre pour "
                        f"une clé dupliquée ({', '.join(table.primary_key_columns)})."
                    ),
                )
            )
        if table.rows_without_usable_key:
            findings.append(
                Finding(
                    code="TABLE_ROW_WITHOUT_USABLE_KEY",
                    severity=Severity.BLOCKING,
                    table=table.name,
                    row_id="*",
                    message=(
                        f"{table.rows_without_usable_key} ligne(s) avec une clé "
                        f"primaire NULL ({', '.join(table.primary_key_columns)})."
                    ),
                )
            )
    return tuple(findings)


@dataclass(frozen=True, slots=True)
class MigrationInventoryReport:
    database: DatabaseInventory
    generic_findings: tuple[Finding, ...] = field(default_factory=tuple)
    expense: ExpenseInventoryResult | None = None

    @property
    def all_findings(self) -> tuple[Finding, ...]:
        if self.expense is None:
            return self.generic_findings
        return self.generic_findings + self.expense.findings

    @property
    def blocking_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.all_findings if f.severity is Severity.BLOCKING)

    @property
    def review_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.all_findings if f.severity is Severity.REVIEW)

    @property
    def info_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.all_findings if f.severity is Severity.INFO)

    @property
    def decision(self) -> str:
        return REVIEW_REQUIRED if self.blocking_findings else READY_FOR_MIGRATION_ANALYSIS


def build_migration_inventory_report(
    database: DatabaseInventory,
    *,
    expense: ExpenseInventoryResult | None = None,
) -> MigrationInventoryReport:
    return MigrationInventoryReport(
        database=database,
        generic_findings=_generic_findings(database),
        expense=expense,
    )


def _column_stats_json(stats: ColumnStats) -> dict[str, Any]:
    return {
        "name": stats.column.name,
        "declared_type": stats.column.declared_type,
        "kind": stats.column.kind.value,
        "nullable": stats.column.nullable,
        "is_primary_key": stats.column.is_primary_key,
        "row_count": stats.row_count,
        "null_count": stats.null_count,
        "empty_string_count": stats.empty_string_count,
        "zero_count": stats.zero_count,
        "distinct_count": stats.distinct_count,
        "min_text_length": stats.min_text_length,
        "max_text_length": stats.max_text_length,
        "min_numeric": stats.min_numeric,
        "max_numeric": stats.max_numeric,
        "min_date": stats.min_date,
        "max_date": stats.max_date,
        "sample_values": list(stats.sample_values),
    }


def _table_json(table: TableInventory) -> dict[str, Any]:
    return {
        "name": table.name,
        "row_count": table.row_count,
        "primary_key_columns": list(table.primary_key_columns),
        "rows_without_usable_key": table.rows_without_usable_key,
        "duplicate_key_row_count": table.duplicate_key_row_count,
        "columns": [_column_stats_json(c) for c in table.columns],
    }


def _database_json(database: DatabaseInventory) -> dict[str, Any]:
    return {
        "engine": database.engine,
        "engine_version": database.engine_version,
        "source_label": database.source_label,
        "inventoried_at": database.inventoried_at.isoformat(),
        "source_fingerprint": database.source_fingerprint,
        "table_count": database.table_count,
        "total_row_count": database.total_row_count,
        "tables": [_table_json(t) for t in database.tables],
    }


def _finding_json(finding: Finding) -> dict[str, Any]:
    return {
        "code": finding.code,
        "severity": finding.severity.value,
        "table": finding.table,
        "row_id": finding.row_id,
        "column": finding.column,
        "message": finding.message,
    }


def _expense_json(expense: ExpenseInventoryResult) -> dict[str, Any]:
    summary = expense.summary
    return {
        "trip_count": summary.trip_count,
        "free_trip_count": summary.free_trip_count,
        "attached_trip_count": summary.attached_trip_count,
        "reimbursement_count": summary.reimbursement_count,
        "person_count_used": summary.person_count_used,
        "reimbursement_amount_total": str(summary.reimbursement_amount_total),
        "reimbursement_amount_parsed_count": summary.reimbursement_amount_parsed_count,
        "mirror_audits": [
            {
                "reimbursement_id": str(audit.reimbursement_id),
                "mirror_trip_ids": [str(i) for i in audit.mirror_trip_ids],
                "canonical_trip_ids": [str(i) for i in audit.canonical_trip_ids],
                "mirror_only_trip_ids": [str(i) for i in audit.mirror_only_trip_ids],
                "canonical_only_trip_ids": [str(i) for i in audit.canonical_only_trip_ids],
                "invalid_tokens": list(audit.invalid_tokens),
                "matches": audit.matches,
            }
            for audit in expense.mirror_audits
        ],
    }


def to_json_dict(report: MigrationInventoryReport) -> dict[str, Any]:
    return {
        "database": _database_json(report.database),
        "expense_pilot": _expense_json(report.expense) if report.expense is not None else None,
        "findings": [_finding_json(f) for f in report.all_findings],
        "decision": report.decision,
    }


def _findings_by_severity(findings: tuple[Finding, ...], severity: Severity) -> list[Finding]:
    return sorted(
        (f for f in findings if f.severity is severity),
        key=lambda f: (f.code, f.table, f.row_id),
    )


def _render_finding_group(findings: list[Finding], title: str) -> list[str]:
    if not findings:
        return [f"### {title}", "", "Aucune.", ""]
    lines = [f"### {title}", ""]
    current_code: str | None = None
    for finding in findings:
        if finding.code != current_code:
            current_code = finding.code
            lines.append(f"**{finding.code}**")
        lines.append(f"- `{finding.table}:{finding.row_id}` — {finding.message}")
    lines.append("")
    return lines


def render_markdown(report: MigrationInventoryReport) -> str:
    database = report.database
    all_findings = report.all_findings
    blocking = _findings_by_severity(all_findings, Severity.BLOCKING)
    review = _findings_by_severity(all_findings, Severity.REVIEW)
    info = _findings_by_severity(all_findings, Severity.INFO)

    lines: list[str] = [
        "# Rapport d'inventaire de migration",
        "",
        f"Base inspectée : {database.source_label}",
        f"Moteur : {database.engine} {database.engine_version}",
        f"Tables : {database.table_count}",
        f"Lignes : {database.total_row_count}",
        "",
    ]

    if report.expense is not None:
        summary = report.expense.summary
        lines.extend(
            [
                "Frais",
                "-----",
                f"Personnes utilisées : {summary.person_count_used}",
                (
                    f"Déplacements : {summary.trip_count} "
                    f"(libres : {summary.free_trip_count}, "
                    f"rattachés : {summary.attached_trip_count})"
                ),
                (
                    f"Remboursements : {summary.reimbursement_count} "
                    f"(montant total : {summary.reimbursement_amount_total})"
                ),
                "",
            ]
        )

    lines.extend(
        [
            f"Anomalies bloquantes : {len(blocking)}",
            f"Transformations prévisibles : {len(review)}",
            f"Informations : {len(info)}",
            "",
            "Décision automatique :",
            report.decision,
            "",
            "## Détail des anomalies",
            "",
        ]
    )
    lines.extend(_render_finding_group(blocking, "BLOCKING"))
    lines.extend(_render_finding_group(review, "REVIEW"))
    lines.extend(_render_finding_group(info, "INFO"))

    lines.append("## Tables")
    lines.append("")
    lines.append("| Table | Lignes | Clé primaire | Doublons de clé | Lignes sans clé |")
    lines.append("|---|---:|---|---:|---:|")
    for table in database.tables:
        key = ", ".join(table.primary_key_columns) or "—"
        lines.append(
            f"| `{table.name}` | {table.row_count} | {key} | "
            f"{table.duplicate_key_row_count} | {table.rows_without_usable_key} |"
        )
    lines.append("")

    return "\n".join(lines)
