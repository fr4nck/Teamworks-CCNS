"""Contrats de réconciliation pour les migrations historiques.

Ce module est volontairement indépendant du moteur SQL cible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class MigrationDisposition(str, Enum):
    MIGRATED = "MIGRATED"
    TRANSFORMED = "TRANSFORMED"
    IGNORED = "IGNORED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class MigrationLedgerEntry:
    source_system: str
    source_table: str
    source_id: str
    disposition: MigrationDisposition
    destination_type: str | None = None
    destination_id: str | None = None
    reason_code: str | None = None
    message: str = ""

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.source_system.strip():
            errors.append("source_system obligatoire")
        if not self.source_table.strip():
            errors.append("source_table obligatoire")
        if not str(self.source_id).strip():
            errors.append("source_id obligatoire")
        if self.disposition in {
            MigrationDisposition.MIGRATED,
            MigrationDisposition.TRANSFORMED,
        }:
            if not (self.destination_type or "").strip():
                errors.append("destination_type obligatoire pour une ligne migrée")
            if not (self.destination_id or "").strip():
                errors.append("destination_id obligatoire pour une ligne migrée")
        if self.disposition in {
            MigrationDisposition.TRANSFORMED,
            MigrationDisposition.IGNORED,
            MigrationDisposition.REJECTED,
        } and not (self.reason_code or "").strip():
            errors.append("reason_code obligatoire pour TRANSFORMED/IGNORED/REJECTED")
        return tuple(errors)


@dataclass(frozen=True, slots=True)
class ReconciliationMetric:
    code: str
    source_value: int | str
    destination_value: int | str
    blocking: bool = True

    @property
    def matches(self) -> bool:
        return self.source_value == self.destination_value


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    expected_source_rows: int
    entries: tuple[MigrationLedgerEntry, ...] = field(default_factory=tuple)
    metrics: tuple[ReconciliationMetric, ...] = field(default_factory=tuple)

    @classmethod
    def build(
        cls,
        *,
        expected_source_rows: int,
        entries: Iterable[MigrationLedgerEntry],
        metrics: Iterable[ReconciliationMetric] = (),
    ) -> "ReconciliationReport":
        return cls(
            expected_source_rows=expected_source_rows,
            entries=tuple(entries),
            metrics=tuple(metrics),
        )

    @property
    def explained_rows(self) -> int:
        return len(self.entries)

    @property
    def unexplained_rows(self) -> int:
        return max(0, self.expected_source_rows - self.explained_rows)

    @property
    def rejected_rows(self) -> int:
        return sum(
            entry.disposition is MigrationDisposition.REJECTED
            for entry in self.entries
        )

    @property
    def invalid_entries(self) -> tuple[MigrationLedgerEntry, ...]:
        return tuple(entry for entry in self.entries if entry.validate())

    @property
    def blocking_metric_mismatches(self) -> tuple[ReconciliationMetric, ...]:
        return tuple(
            metric for metric in self.metrics
            if metric.blocking and not metric.matches
        )

    @property
    def duplicated_sources(self) -> tuple[tuple[str, str, str], ...]:
        seen: set[tuple[str, str, str]] = set()
        duplicates: list[tuple[str, str, str]] = []
        for entry in self.entries:
            key = (
                entry.source_system.strip(),
                entry.source_table.strip(),
                str(entry.source_id).strip(),
            )
            if key in seen and key not in duplicates:
                duplicates.append(key)
            seen.add(key)
        return tuple(duplicates)

    @property
    def is_valid(self) -> bool:
        return (
            self.expected_source_rows >= 0
            and self.explained_rows == self.expected_source_rows
            and self.unexplained_rows == 0
            and self.rejected_rows == 0
            and not self.invalid_entries
            and not self.duplicated_sources
            and not self.blocking_metric_mismatches
        )

    def blocking_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.expected_source_rows < 0:
            reasons.append("expected_source_rows ne peut pas être négatif")
        if self.explained_rows != self.expected_source_rows:
            reasons.append(
                "comptage source non réconcilié: "
                f"attendu={self.expected_source_rows}, expliqué={self.explained_rows}"
            )
        if self.rejected_rows:
            reasons.append(f"{self.rejected_rows} ligne(s) rejetée(s)")
        if self.invalid_entries:
            reasons.append(f"{len(self.invalid_entries)} entrée(s) de journal invalide(s)")
        if self.duplicated_sources:
            reasons.append(f"{len(self.duplicated_sources)} identité(s) source dupliquée(s)")
        if self.blocking_metric_mismatches:
            reasons.append(
                f"{len(self.blocking_metric_mismatches)} métrique(s) bloquante(s) en écart"
            )
        return tuple(reasons)
