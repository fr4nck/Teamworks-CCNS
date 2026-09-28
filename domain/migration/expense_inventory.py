"""Inventaire spécialisé du pilote Frais / remboursements.

Contrairement à expense_pilot.reconcile_expenses, ce module n'a besoin
d'aucune donnée destination : il analyse uniquement la base source pour
répondre, avant toute migration, à la question « que contient réellement
cette base et quelles anomalies contient-elle ? ».

Les valeurs sources sont volontairement typées `object` : une base
historique réelle peut contenir des valeurs non conformes (dates
illisibles, montants non numériques, ...) qu'il faut détecter, pas
supposer absentes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable

from domain.migration.expense_pilot import (
    MirrorAudit,
    normalize_reimbursement_id,
    parse_legacy_trip_list,
)
from domain.migration.finding import Finding
from domain.migration.severity import Severity

_DATE_FORMATS: tuple[str, ...] = ("%Y-%m-%d", "%d/%m/%Y")

_USUAL_ROUND_TRIP_VALUES = (0, 1, "0", "1", True, False, None, "", "True", "False")


@dataclass(frozen=True, slots=True)
class RawTripRow:
    trip_id: object
    person_id: object
    travel_date: object
    departure_postcode: object
    arrival_postcode: object
    distance: object
    tariff_per_km: object
    round_trip: object
    reimbursement_id: object


@dataclass(frozen=True, slots=True)
class RawReimbursementRow:
    reimbursement_id: object
    person_id: object
    payment_date: object
    amount: object
    legacy_trip_list: object


@dataclass(frozen=True, slots=True)
class ExpenseInventorySummary:
    trip_count: int
    free_trip_count: int
    attached_trip_count: int
    reimbursement_count: int
    person_count_used: int
    reimbursement_amount_total: Decimal
    reimbursement_amount_parsed_count: int


@dataclass(frozen=True, slots=True)
class ExpenseInventoryResult:
    summary: ExpenseInventorySummary
    findings: tuple[Finding, ...] = field(default_factory=tuple)
    mirror_audits: tuple[MirrorAudit, ...] = field(default_factory=tuple)

    @property
    def blocking_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.BLOCKING)

    @property
    def review_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.REVIEW)

    @property
    def info_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.INFO)


def _try_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _try_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _postcode_findings(*, table: str, row_id: str, label: str, value: object) -> list[Finding]:
    text = "" if value is None else str(value).strip()
    if not text:
        return []
    if len(text) != 5:
        return [
            Finding(
                code="TRIP_POSTCODE_LENGTH_INVALID",
                severity=Severity.REVIEW,
                table=table,
                row_id=row_id,
                column=f"cp_{label}",
                message=f"Code postal {label} de longueur {len(text)} au lieu de 5.",
            )
        ]
    if not text.isdigit():
        return [
            Finding(
                code="TRIP_POSTCODE_NOT_NUMERIC",
                severity=Severity.REVIEW,
                table=table,
                row_id=row_id,
                column=f"cp_{label}",
                message=f"Code postal {label} contient des caractères non numériques.",
            )
        ]
    if text.startswith("0"):
        return [
            Finding(
                code="TRIP_POSTCODE_LEADING_ZERO",
                severity=Severity.INFO,
                table=table,
                row_id=row_id,
                column=f"cp_{label}",
                message=f"Code postal {label} commence par zéro, à conserver comme texte.",
            )
        ]
    return []


def analyze_expense_pilot_source(
    *,
    source_people_ids: Iterable[object],
    trips: Iterable[RawTripRow],
    reimbursements: Iterable[RawReimbursementRow],
) -> ExpenseInventoryResult:
    people = set(source_people_ids)
    trip_list = tuple(trips)
    reimbursement_list = tuple(reimbursements)

    findings: list[Finding] = []

    trip_id_counts = Counter(trip.trip_id for trip in trip_list)
    for trip_id, count in trip_id_counts.items():
        if count > 1:
            findings.append(
                Finding(
                    code="TRIP_ID_DUPLICATED",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=str(trip_id),
                    message=f"{count} lignes deplacements partagent IDdeplacement={trip_id}.",
                )
            )

    reimbursement_id_counts = Counter(item.reimbursement_id for item in reimbursement_list)
    for reimbursement_id, count in reimbursement_id_counts.items():
        if count > 1:
            findings.append(
                Finding(
                    code="REIMBURSEMENT_ID_DUPLICATED",
                    severity=Severity.BLOCKING,
                    table="remboursements",
                    row_id=str(reimbursement_id),
                    message=(
                        f"{count} lignes remboursements partagent "
                        f"IDremboursement={reimbursement_id}."
                    ),
                )
            )

    valid_reimbursement_ids = {item.reimbursement_id for item in reimbursement_list}
    reimbursement_by_id = {item.reimbursement_id: item for item in reimbursement_list}
    trip_by_id = {trip.trip_id: trip for trip in trip_list}

    canonical_by_reimbursement: dict[object, list[object]] = {}
    free_trip_count = 0
    attached_trip_count = 0
    people_used: set[object] = set()

    for trip in trip_list:
        row_id = str(trip.trip_id)
        people_used.add(trip.person_id)

        if trip.person_id not in people:
            findings.append(
                Finding(
                    code="TRIP_PERSON_NOT_FOUND",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=row_id,
                    column="IDpersonne",
                    message="IDpersonne du déplacement absent du référentiel personnes.",
                )
            )

        try:
            reimbursement_id = normalize_reimbursement_id(trip.reimbursement_id)
        except ValueError:
            findings.append(
                Finding(
                    code="TRIP_REIMBURSEMENT_ID_INVALID",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=row_id,
                    column="IDremboursement",
                    message=f"IDremboursement={trip.reimbursement_id!r} invalide (négatif ou non entier).",
                )
            )
            reimbursement_id = None
        else:
            if trip.reimbursement_id in (0, "0"):
                findings.append(
                    Finding(
                        code="ZERO_REIMBURSEMENT_NORMALIZED_TO_NULL",
                        severity=Severity.INFO,
                        table="deplacements",
                        row_id=row_id,
                        column="IDremboursement",
                        message="IDremboursement=0 sera normalisé en absence de rattachement.",
                    )
                )

        if reimbursement_id is None:
            free_trip_count += 1
        else:
            attached_trip_count += 1
            if reimbursement_id not in valid_reimbursement_ids:
                findings.append(
                    Finding(
                        code="TRIP_REIMBURSEMENT_NOT_FOUND",
                        severity=Severity.BLOCKING,
                        table="deplacements",
                        row_id=row_id,
                        column="IDremboursement",
                        message="Le déplacement référence un remboursement source inexistant.",
                    )
                )
            else:
                parent = reimbursement_by_id[reimbursement_id]
                if parent.person_id != trip.person_id:
                    findings.append(
                        Finding(
                            code="TRIP_REIMBURSEMENT_PERSON_MISMATCH",
                            severity=Severity.BLOCKING,
                            table="deplacements",
                            row_id=row_id,
                            message=(
                                "Déplacement et remboursement appartiennent à des "
                                "personnes différentes."
                            ),
                        )
                    )
                canonical_by_reimbursement.setdefault(reimbursement_id, []).append(
                    trip.trip_id
                )

        findings.extend(
            _postcode_findings(
                table="deplacements",
                row_id=row_id,
                label="depart",
                value=trip.departure_postcode,
            )
        )
        findings.extend(
            _postcode_findings(
                table="deplacements",
                row_id=row_id,
                label="arrivee",
                value=trip.arrival_postcode,
            )
        )

        distance = _try_decimal(trip.distance)
        if distance is None:
            findings.append(
                Finding(
                    code="TRIP_DISTANCE_UNPARSABLE",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=row_id,
                    column="distance",
                    message=f"distance={trip.distance!r} non interprétable comme décimal.",
                )
            )
        elif distance < 0:
            findings.append(
                Finding(
                    code="TRIP_DISTANCE_NEGATIVE",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=row_id,
                    column="distance",
                    message=f"distance négative ({distance}).",
                )
            )

        tariff = _try_decimal(trip.tariff_per_km)
        if tariff is None:
            findings.append(
                Finding(
                    code="TRIP_TARIFF_UNPARSABLE",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=row_id,
                    column="tarif_km",
                    message=f"tarif_km={trip.tariff_per_km!r} non interprétable comme décimal.",
                )
            )
        elif tariff < 0:
            findings.append(
                Finding(
                    code="TRIP_TARIFF_NEGATIVE",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=row_id,
                    column="tarif_km",
                    message=f"tarif_km négatif ({tariff}).",
                )
            )

        if _try_date(trip.travel_date) is None:
            findings.append(
                Finding(
                    code="TRIP_DATE_UNPARSABLE",
                    severity=Severity.BLOCKING,
                    table="deplacements",
                    row_id=row_id,
                    column="date",
                    message=f"date={trip.travel_date!r} non interprétable.",
                )
            )

        if trip.round_trip not in _USUAL_ROUND_TRIP_VALUES:
            findings.append(
                Finding(
                    code="TRIP_ROUND_TRIP_VALUE_UNUSUAL",
                    severity=Severity.REVIEW,
                    table="deplacements",
                    row_id=row_id,
                    column="aller_retour",
                    message=f"aller_retour={trip.round_trip!r} ne correspond à aucune valeur connue.",
                )
            )

    mirror_audits: list[MirrorAudit] = []
    amount_total = Decimal("0")
    amount_parsed_count = 0

    for reimbursement in reimbursement_list:
        row_id = str(reimbursement.reimbursement_id)
        people_used.add(reimbursement.person_id)

        if reimbursement.person_id not in people:
            findings.append(
                Finding(
                    code="REIMBURSEMENT_PERSON_NOT_FOUND",
                    severity=Severity.BLOCKING,
                    table="remboursements",
                    row_id=row_id,
                    column="IDpersonne",
                    message="IDpersonne du remboursement absent du référentiel personnes.",
                )
            )

        amount = _try_decimal(reimbursement.amount)
        if amount is None:
            findings.append(
                Finding(
                    code="REIMBURSEMENT_AMOUNT_UNPARSABLE",
                    severity=Severity.BLOCKING,
                    table="remboursements",
                    row_id=row_id,
                    column="montant",
                    message=f"montant={reimbursement.amount!r} non interprétable comme décimal.",
                )
            )
        else:
            amount_total += amount
            amount_parsed_count += 1
            if amount < 0:
                findings.append(
                    Finding(
                        code="REIMBURSEMENT_AMOUNT_NEGATIVE",
                        severity=Severity.BLOCKING,
                        table="remboursements",
                        row_id=row_id,
                        column="montant",
                        message=f"montant négatif ({amount}).",
                    )
                )
            elif amount == 0:
                findings.append(
                    Finding(
                        code="REIMBURSEMENT_AMOUNT_ZERO",
                        severity=Severity.REVIEW,
                        table="remboursements",
                        row_id=row_id,
                        column="montant",
                        message="montant égal à zéro.",
                    )
                )

        if _try_date(reimbursement.payment_date) is None:
            findings.append(
                Finding(
                    code="REIMBURSEMENT_DATE_UNPARSABLE",
                    severity=Severity.BLOCKING,
                    table="remboursements",
                    row_id=row_id,
                    column="date",
                    message=f"date={reimbursement.payment_date!r} non interprétable.",
                )
            )

        mirror_ids, invalid_tokens = parse_legacy_trip_list(reimbursement.legacy_trip_list)
        canonical_ids = tuple(
            sorted(canonical_by_reimbursement.get(reimbursement.reimbursement_id, ()))
        )
        mirror_set = set(mirror_ids)
        canonical_set = set(canonical_ids)
        mirror_only = tuple(sorted(mirror_set - canonical_set))
        canonical_only = tuple(sorted(canonical_set - mirror_set))
        audit = MirrorAudit(
            reimbursement_id=reimbursement.reimbursement_id,
            mirror_trip_ids=tuple(sorted(mirror_set)),
            canonical_trip_ids=canonical_ids,
            mirror_only_trip_ids=mirror_only,
            canonical_only_trip_ids=canonical_only,
            invalid_tokens=invalid_tokens,
        )
        mirror_audits.append(audit)

        if invalid_tokens:
            findings.append(
                Finding(
                    code="LEGACY_TRIP_LIST_UNPARSABLE",
                    severity=Severity.BLOCKING,
                    table="remboursements",
                    row_id=row_id,
                    column="listeIDdeplacement",
                    message=(
                        "La liste historique contient des identifiants non "
                        f"interprétables : {invalid_tokens}."
                    ),
                )
            )
        elif mirror_only:
            unknown = [trip_id for trip_id in mirror_only if trip_id not in trip_by_id]
            if unknown:
                findings.append(
                    Finding(
                        code="LEGACY_TRIP_LIST_REFERENCES_UNKNOWN_TRIP",
                        severity=Severity.BLOCKING,
                        table="remboursements",
                        row_id=row_id,
                        column="listeIDdeplacement",
                        message=(
                            "Le miroir historique référence un déplacement source "
                            f"inexistant : {unknown}."
                        ),
                    )
                )
            else:
                mismatched = [
                    trip_id
                    for trip_id in mirror_only
                    if trip_by_id[trip_id].person_id != reimbursement.person_id
                ]
                if mismatched:
                    findings.append(
                        Finding(
                            code="LEGACY_TRIP_LIST_PERSON_MISMATCH",
                            severity=Severity.BLOCKING,
                            table="remboursements",
                            row_id=row_id,
                            column="listeIDdeplacement",
                            message=(
                                "Le miroir historique référence un déplacement "
                                f"d'une autre personne : {mismatched}."
                            ),
                        )
                    )
                else:
                    findings.append(
                        Finding(
                            code="LEGACY_TRIP_LIST_CONFLICTS_WITH_CANONICAL_ASSIGNMENT",
                            severity=Severity.BLOCKING,
                            table="remboursements",
                            row_id=row_id,
                            column="listeIDdeplacement",
                            message=(
                                "Le miroir historique revendique un déplacement que "
                                "deplacements.IDremboursement n'attribue pas à ce "
                                "remboursement."
                            ),
                        )
                    )
        elif canonical_only:
            findings.append(
                Finding(
                    code="LEGACY_TRIP_LIST_REBUILT_FROM_CANONICAL_ASSIGNMENTS",
                    severity=Severity.REVIEW,
                    table="remboursements",
                    row_id=row_id,
                    column="listeIDdeplacement",
                    message=(
                        "Le miroir listeIDdeplacement est incomplet mais "
                        "reconstructible depuis deplacements.IDremboursement."
                    ),
                )
            )

    summary = ExpenseInventorySummary(
        trip_count=len(trip_list),
        free_trip_count=free_trip_count,
        attached_trip_count=attached_trip_count,
        reimbursement_count=len(reimbursement_list),
        person_count_used=len(people_used),
        reimbursement_amount_total=amount_total,
        reimbursement_amount_parsed_count=amount_parsed_count,
    )

    return ExpenseInventoryResult(
        summary=summary,
        findings=tuple(findings),
        mirror_audits=tuple(mirror_audits),
    )
