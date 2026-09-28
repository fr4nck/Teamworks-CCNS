"""Contrôles de réconciliation du pilote Frais.

La relation canonique historique est deplacements.IDremboursement.
Le champ remboursements.listeIDdeplacement est un miroir audité.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable

from domain.migration.reconciliation import (
    MigrationDisposition,
    MigrationLedgerEntry,
    ReconciliationMetric,
    ReconciliationReport,
)


@dataclass(frozen=True, slots=True)
class LegacyTrip:
    trip_id: int
    person_id: int
    travel_date: date
    purpose: str
    departure_postcode: str
    departure_city: str
    arrival_postcode: str
    arrival_city: str
    distance: Decimal
    round_trip: bool
    tariff_per_km: Decimal
    reimbursement_id: int | None


@dataclass(frozen=True, slots=True)
class LegacyReimbursement:
    reimbursement_id: int
    person_id: int
    payment_date: date
    amount: Decimal
    legacy_trip_list: str | None


@dataclass(frozen=True, slots=True)
class CanonicalTrip:
    source_trip_id: int
    destination_id: str
    person_id: int
    travel_date: date
    purpose: str
    departure_postcode: str
    departure_city: str
    arrival_postcode: str
    arrival_city: str
    distance: Decimal
    round_trip: bool
    tariff_per_km: Decimal
    source_reimbursement_id: int | None


@dataclass(frozen=True, slots=True)
class CanonicalReimbursement:
    source_reimbursement_id: int
    destination_id: str
    person_id: int
    payment_date: date
    amount: Decimal
    source_trip_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class MirrorAudit:
    reimbursement_id: int
    mirror_trip_ids: tuple[int, ...]
    canonical_trip_ids: tuple[int, ...]
    mirror_only_trip_ids: tuple[int, ...]
    canonical_only_trip_ids: tuple[int, ...]
    invalid_tokens: tuple[str, ...] = ()

    @property
    def matches(self) -> bool:
        return (
            not self.invalid_tokens
            and not self.mirror_only_trip_ids
            and not self.canonical_only_trip_ids
        )


@dataclass(frozen=True, slots=True)
class ExpenseReconciliationResult:
    report: ReconciliationReport
    mirror_audits: tuple[MirrorAudit, ...]

    @property
    def is_valid(self) -> bool:
        return self.report.is_valid


def normalize_reimbursement_id(value: object) -> int | None:
    if isinstance(value, bool):
        raise ValueError("IDremboursement booléen invalide")
    if value in (None, "", 0, "0"):
        return None
    result = int(value)
    if result <= 0:
        raise ValueError("IDremboursement doit être positif ou nul")
    return result


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"valeur décimale invalide: {value!r}") from exc


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_legacy_trip_list(value: object) -> tuple[tuple[int, ...], tuple[str, ...]]:
    if value is None or str(value).strip() == "":
        return (), ()
    parsed: list[int] = []
    invalid: list[str] = []
    for raw in str(value).strip().split("-"):
        token = raw.strip()
        if not token:
            continue
        try:
            item = int(token)
        except ValueError:
            invalid.append(token)
            continue
        if item <= 0:
            invalid.append(token)
            continue
        parsed.append(item)
    return tuple(parsed), tuple(invalid)


def _trip_values_match(source: LegacyTrip, dest: CanonicalTrip) -> bool:
    return (
        source.person_id == dest.person_id
        and source.travel_date == dest.travel_date
        and _text(source.purpose) == _text(dest.purpose)
        and _text(source.departure_postcode) == _text(dest.departure_postcode)
        and _text(source.departure_city) == _text(dest.departure_city)
        and _text(source.arrival_postcode) == _text(dest.arrival_postcode)
        and _text(source.arrival_city) == _text(dest.arrival_city)
        and _decimal(source.distance) == _decimal(dest.distance)
        and bool(source.round_trip) is bool(dest.round_trip)
        and _decimal(source.tariff_per_km) == _decimal(dest.tariff_per_km)
        and normalize_reimbursement_id(source.reimbursement_id)
        == normalize_reimbursement_id(dest.source_reimbursement_id)
    )


def _reimbursement_values_match(
    source: LegacyReimbursement,
    dest: CanonicalReimbursement,
    canonical_trip_ids: tuple[int, ...],
) -> bool:
    return (
        source.person_id == dest.person_id
        and source.payment_date == dest.payment_date
        and _decimal(source.amount) == _decimal(dest.amount)
        and tuple(sorted(canonical_trip_ids)) == tuple(sorted(dest.source_trip_ids))
    )


def reconcile_expenses(
    *,
    source_people_ids: Iterable[int],
    source_trips: Iterable[LegacyTrip],
    source_reimbursements: Iterable[LegacyReimbursement],
    destination_trips: Iterable[CanonicalTrip],
    destination_reimbursements: Iterable[CanonicalReimbursement],
) -> ExpenseReconciliationResult:
    people = set(source_people_ids)
    trips = tuple(source_trips)
    reimbursements = tuple(source_reimbursements)
    destination_trip_items = tuple(destination_trips)
    destination_reimbursement_items = tuple(destination_reimbursements)
    dest_trips = {item.source_trip_id: item for item in destination_trip_items}
    dest_reimbursements = {
        item.source_reimbursement_id: item
        for item in destination_reimbursement_items
    }
    source_reimbursement_ids = {item.reimbursement_id for item in reimbursements}

    canonical_by_reimbursement: dict[int, list[int]] = {}
    for trip in trips:
        reimbursement_id = normalize_reimbursement_id(trip.reimbursement_id)
        if reimbursement_id is not None:
            canonical_by_reimbursement.setdefault(reimbursement_id, []).append(trip.trip_id)

    source_trips_by_id = {item.trip_id: item for item in trips}

    mirror_audits: list[MirrorAudit] = []
    mirror_by_reimbursement: dict[int, MirrorAudit] = {}
    for reimbursement in reimbursements:
        mirror_ids, invalid = parse_legacy_trip_list(reimbursement.legacy_trip_list)
        canonical_ids = tuple(sorted(canonical_by_reimbursement.get(reimbursement.reimbursement_id, ())))
        mirror_set = set(mirror_ids)
        canonical_set = set(canonical_ids)
        audit = MirrorAudit(
            reimbursement_id=reimbursement.reimbursement_id,
            mirror_trip_ids=tuple(sorted(mirror_set)),
            canonical_trip_ids=canonical_ids,
            mirror_only_trip_ids=tuple(sorted(mirror_set - canonical_set)),
            canonical_only_trip_ids=tuple(sorted(canonical_set - mirror_set)),
            invalid_tokens=invalid,
        )
        mirror_audits.append(audit)
        mirror_by_reimbursement[reimbursement.reimbursement_id] = audit

    entries: list[MigrationLedgerEntry] = []

    for trip in trips:
        reason = None
        message = ""
        disposition = MigrationDisposition.MIGRATED
        destination = dest_trips.get(trip.trip_id)
        reimbursement_id = normalize_reimbursement_id(trip.reimbursement_id)

        if trip.person_id not in people:
            disposition = MigrationDisposition.REJECTED
            reason = "TRIP_PERSON_NOT_FOUND"
            message = "IDpersonne du déplacement absent du référentiel source."
        elif reimbursement_id is not None and reimbursement_id not in source_reimbursement_ids:
            disposition = MigrationDisposition.REJECTED
            reason = "TRIP_REIMBURSEMENT_NOT_FOUND"
            message = "Le déplacement référence un remboursement source inexistant."
        elif reimbursement_id is not None:
            reimbursement = next(
                item for item in reimbursements if item.reimbursement_id == reimbursement_id
            )
            if reimbursement.person_id != trip.person_id:
                disposition = MigrationDisposition.REJECTED
                reason = "TRIP_REIMBURSEMENT_PERSON_MISMATCH"
                message = "Déplacement et remboursement appartiennent à des personnes différentes."
        if disposition is not MigrationDisposition.REJECTED:
            if destination is None:
                disposition = MigrationDisposition.REJECTED
                reason = "TRIP_DESTINATION_MISSING"
                message = "Aucun déplacement destination correspondant."
            elif not _trip_values_match(trip, destination):
                disposition = MigrationDisposition.REJECTED
                reason = "TRIP_VALUE_MISMATCH"
                message = "Les valeurs du déplacement source et destination divergent."
            elif trip.reimbursement_id in (0, "0"):
                disposition = MigrationDisposition.TRANSFORMED
                reason = "ZERO_REIMBURSEMENT_NORMALIZED_TO_NULL"
                message = "Le pseudo-NULL historique 0 a été normalisé en absence de rattachement."

        entries.append(
            MigrationLedgerEntry(
                source_system="noethys_teamworks_legacy",
                source_table="deplacements",
                source_id=str(trip.trip_id),
                disposition=disposition,
                destination_type="expense_trip" if destination is not None else None,
                destination_id=destination.destination_id if destination is not None else None,
                reason_code=reason,
                message=message,
            )
        )

    for reimbursement in reimbursements:
        reason = None
        message = ""
        disposition = MigrationDisposition.MIGRATED
        destination = dest_reimbursements.get(reimbursement.reimbursement_id)
        canonical_ids = tuple(sorted(canonical_by_reimbursement.get(reimbursement.reimbursement_id, ())))
        audit = mirror_by_reimbursement[reimbursement.reimbursement_id]

        if reimbursement.person_id not in people:
            disposition = MigrationDisposition.REJECTED
            reason = "REIMBURSEMENT_PERSON_NOT_FOUND"
            message = "IDpersonne du remboursement absent du référentiel source."
        elif destination is None:
            disposition = MigrationDisposition.REJECTED
            reason = "REIMBURSEMENT_DESTINATION_MISSING"
            message = "Aucun remboursement destination correspondant."
        elif not _reimbursement_values_match(reimbursement, destination, canonical_ids):
            disposition = MigrationDisposition.REJECTED
            reason = "REIMBURSEMENT_VALUE_MISMATCH"
            message = "Les valeurs ou rattachements du remboursement divergent."
        elif audit.invalid_tokens:
            disposition = MigrationDisposition.REJECTED
            reason = "LEGACY_TRIP_LIST_UNPARSABLE"
            message = "La liste historique contient des identifiants non interprétables."
        elif audit.mirror_only_trip_ids:
            mirror_only_trips = [
                source_trips_by_id.get(trip_id)
                for trip_id in audit.mirror_only_trip_ids
            ]
            if any(item is None for item in mirror_only_trips):
                disposition = MigrationDisposition.REJECTED
                reason = "LEGACY_TRIP_LIST_REFERENCES_UNKNOWN_TRIP"
                message = "Le miroir historique référence un déplacement source inexistant."
            elif any(item.person_id != reimbursement.person_id for item in mirror_only_trips):
                disposition = MigrationDisposition.REJECTED
                reason = "LEGACY_TRIP_LIST_PERSON_MISMATCH"
                message = "Le miroir historique référence un déplacement d'une autre personne."
            else:
                disposition = MigrationDisposition.REJECTED
                reason = "LEGACY_TRIP_LIST_CONFLICTS_WITH_CANONICAL_ASSIGNMENT"
                message = (
                    "Le miroir historique revendique un déplacement que "
                    "deplacements.IDremboursement n'attribue pas à ce remboursement."
                )
        elif audit.canonical_only_trip_ids:
            # Un miroir incomplet est reconstructible depuis la relation canonique.
            disposition = MigrationDisposition.TRANSFORMED
            reason = "LEGACY_TRIP_LIST_REBUILT_FROM_CANONICAL_ASSIGNMENTS"
            message = (
                "Le miroir listeIDdeplacement a été reconstruit depuis "
                "deplacements.IDremboursement."
            )

        entries.append(
            MigrationLedgerEntry(
                source_system="noethys_teamworks_legacy",
                source_table="remboursements",
                source_id=str(reimbursement.reimbursement_id),
                disposition=disposition,
                destination_type="expense_reimbursement" if destination is not None else None,
                destination_id=destination.destination_id if destination is not None else None,
                reason_code=reason,
                message=message,
            )
        )

    source_total_cents = sum(
        int((_decimal(item.amount) * 100).quantize(Decimal("1")))
        for item in reimbursements
    )
    destination_total_cents = sum(
        int((_decimal(item.amount) * 100).quantize(Decimal("1")))
        for item in dest_reimbursements.values()
    )
    source_free = sum(
        normalize_reimbursement_id(item.reimbursement_id) is None for item in trips
    )
    destination_free = sum(
        normalize_reimbursement_id(item.source_reimbursement_id) is None
        for item in dest_trips.values()
    )

    metrics: list[ReconciliationMetric] = [
        ReconciliationMetric("TRIP_COUNT", len(trips), len(destination_trip_items)),
        ReconciliationMetric(
            "REIMBURSEMENT_COUNT",
            len(reimbursements),
            len(destination_reimbursement_items),
        ),
        ReconciliationMetric(
            "DESTINATION_TRIP_SOURCE_IDS_UNIQUE",
            len(destination_trip_items),
            len(dest_trips),
        ),
        ReconciliationMetric(
            "DESTINATION_REIMBURSEMENT_SOURCE_IDS_UNIQUE",
            len(destination_reimbursement_items),
            len(dest_reimbursements),
        ),
        ReconciliationMetric("FREE_TRIP_COUNT", source_free, destination_free),
        ReconciliationMetric(
            "ATTACHED_TRIP_COUNT",
            len(trips) - source_free,
            len(destination_trip_items) - destination_free,
        ),
        ReconciliationMetric(
            "REIMBURSEMENT_TOTAL_CENTS",
            source_total_cents,
            destination_total_cents,
        ),
    ]

    all_people = sorted(
        set(item.person_id for item in trips)
        | set(item.person_id for item in reimbursements)
        | set(item.person_id for item in destination_trip_items)
        | set(item.person_id for item in destination_reimbursement_items)
    )
    for person_id in all_people:
        metrics.append(
            ReconciliationMetric(
                f"TRIP_COUNT_PERSON_{person_id}",
                sum(item.person_id == person_id for item in trips),
                sum(item.person_id == person_id for item in destination_trip_items),
            )
        )
        metrics.append(
            ReconciliationMetric(
                f"REIMBURSEMENT_COUNT_PERSON_{person_id}",
                sum(item.person_id == person_id for item in reimbursements),
                sum(
                    item.person_id == person_id
                    for item in destination_reimbursement_items
                ),
            )
        )

    all_reimbursement_ids = sorted(
        set(canonical_by_reimbursement)
        | set(item.source_reimbursement_id for item in destination_reimbursement_items)
    )
    for reimbursement_id in all_reimbursement_ids:
        metrics.append(
            ReconciliationMetric(
                f"TRIP_COUNT_REIMBURSEMENT_{reimbursement_id}",
                len(canonical_by_reimbursement.get(reimbursement_id, ())),
                sum(
                    item.source_reimbursement_id == reimbursement_id
                    for item in destination_trip_items
                ),
            )
        )

    if trips and destination_trip_items:
        metrics.extend(
            (
                ReconciliationMetric(
                    "TRIP_MIN_DATE",
                    min(item.travel_date for item in trips).isoformat(),
                    min(item.travel_date for item in destination_trip_items).isoformat(),
                ),
                ReconciliationMetric(
                    "TRIP_MAX_DATE",
                    max(item.travel_date for item in trips).isoformat(),
                    max(item.travel_date for item in destination_trip_items).isoformat(),
                ),
            )
        )
    if reimbursements and destination_reimbursement_items:
        metrics.extend(
            (
                ReconciliationMetric(
                    "REIMBURSEMENT_MIN_DATE",
                    min(item.payment_date for item in reimbursements).isoformat(),
                    min(
                        item.payment_date for item in destination_reimbursement_items
                    ).isoformat(),
                ),
                ReconciliationMetric(
                    "REIMBURSEMENT_MAX_DATE",
                    max(item.payment_date for item in reimbursements).isoformat(),
                    max(
                        item.payment_date for item in destination_reimbursement_items
                    ).isoformat(),
                ),
            )
        )

    report = ReconciliationReport.build(
        expected_source_rows=len(trips) + len(reimbursements),
        entries=entries,
        metrics=tuple(metrics),
    )
    return ExpenseReconciliationResult(
        report=report,
        mirror_audits=tuple(mirror_audits),
    )
