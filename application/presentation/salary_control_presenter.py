from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional
from uuid import UUID

from application.control import ContractSalaryControlConsultationApplicationResult
from domain.contracts.contract_salary_control_projection import ContractSalaryControlRow, ContractSalaryControlStatus
from domain.contracts.contract_salary_evaluation import ContractSalaryEvaluationFailureReason, _strict_date
from domain.convention import ApplicableSalaryMinimumSource
from domain.convention.smic import SmicTerritory

_CENT = Decimal("0.01")
_ZERO = Decimal("0.00")


class ContractSalaryControlPresentationStatus(str, Enum):
    """Statut purement visuel du contrôle salarial présenté."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class ContractSalaryControlPaginationViewModel:
    offset: int
    limit: Optional[int]
    has_previous_page: bool
    has_next_page: bool
    previous_offset: Optional[int]
    next_offset: Optional[int]
    first_displayed_index: Optional[int]
    last_displayed_index: Optional[int]
    total_filtered_count: int
    range_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryControlRowViewModel:
    id: UUID
    contract_id: UUID
    contract_id_label: str
    employee_id: Optional[UUID]
    employee_id_label: str
    reference_date: date
    reference_date_label: str
    status: ContractSalaryControlStatus
    status_label: str
    classification_code: Optional[str]
    classification_code_label: str
    remuneration_amount: Optional[Decimal]
    remuneration_amount_label: str
    applicable_minimum_amount: Optional[Decimal]
    applicable_minimum_amount_label: str
    shortfall_amount: Decimal
    shortfall_amount_label: str
    minimum_source: Optional[ApplicableSalaryMinimumSource]
    minimum_source_label: str
    territory: Optional[SmicTerritory]
    territory_label: str
    failure_reason: Optional[ContractSalaryEvaluationFailureReason]
    failure_reason_label: str
    failure_message: Optional[str]
    failure_message_label: str
    issue_code: Optional[str]
    issue_code_label: str
    issue_message: Optional[str]
    issue_message_label: str


@dataclass(frozen=True, slots=True)
class ContractSalaryControlEmptyStateViewModel:
    title: str
    message: str


@dataclass(frozen=True, slots=True)
class ContractSalaryControlViewModel:
    reference_date: date
    reference_date_label: str
    rows: tuple[ContractSalaryControlRowViewModel, ...]
    global_total_count: int
    global_compliant_count: int
    global_non_compliant_count: int
    global_not_evaluated_count: int
    filtered_total_count: int
    returned_count: int
    filtered_total_shortfall_amount: Decimal
    filtered_total_shortfall_amount_label: str
    global_valid: bool
    filtered_valid: bool
    presentation_status: ContractSalaryControlPresentationStatus
    summary_title: str
    summary_message: str
    pagination: ContractSalaryControlPaginationViewModel
    empty_state: Optional[ContractSalaryControlEmptyStateViewModel]


@dataclass(frozen=True, slots=True)
class ContractSalaryControlPresenter:
    """Présentateur pur et stateless du résultat applicatif de contrôle salarial."""

    def present(
        self,
        result: ContractSalaryControlConsultationApplicationResult,
    ) -> ContractSalaryControlViewModel:
        if type(result) is not ContractSalaryControlConsultationApplicationResult:
            raise TypeError("result doit être un ContractSalaryControlConsultationApplicationResult.")
        rows = tuple(_present_row(row) for row in result.rows)
        status = _presentation_status(result)
        title, message = _summary(result, status)
        empty_state = _empty_state(result, status)
        return ContractSalaryControlViewModel(
            reference_date=result.reference_date,
            reference_date_label=format_french_date(result.reference_date),
            rows=rows,
            global_total_count=result.global_total_count,
            global_compliant_count=result.global_compliant_count,
            global_non_compliant_count=result.global_non_compliant_count,
            global_not_evaluated_count=result.global_not_evaluated_count,
            filtered_total_count=result.filtered_total_count,
            returned_count=result.returned_count,
            filtered_total_shortfall_amount=result.filtered_total_shortfall_amount,
            filtered_total_shortfall_amount_label=format_euro_amount(result.filtered_total_shortfall_amount),
            global_valid=result.global_valid,
            filtered_valid=result.filtered_valid,
            presentation_status=status,
            summary_title=title,
            summary_message=message,
            pagination=_pagination(result),
            empty_state=empty_state,
        )


def format_euro_amount(amount: Decimal) -> str:
    if type(amount) is not Decimal:
        raise TypeError("amount doit être un Decimal strict.")
    quantized = amount.quantize(_CENT, rounding=ROUND_HALF_UP)
    sign = "-" if quantized < _ZERO else ""
    absolute = abs(quantized)
    integer, cents = f"{absolute:.2f}".split(".")
    groups = []
    while integer:
        groups.append(integer[-3:])
        integer = integer[:-3]
    return f"{sign}{' '.join(reversed(groups))},{cents} €"


def format_french_date(value: date) -> str:
    _strict_date(value)
    return value.strftime("%d/%m/%Y")


def _present_row(row: ContractSalaryControlRow) -> ContractSalaryControlRowViewModel:
    if type(row) is not ContractSalaryControlRow:
        raise TypeError("rows doit contenir des ContractSalaryControlRow.")
    return ContractSalaryControlRowViewModel(
        id=row.id,
        contract_id=row.contract_id,
        contract_id_label=str(row.contract_id),
        employee_id=row.employee_id,
        employee_id_label=str(row.employee_id) if row.employee_id is not None else "Non renseigné",
        reference_date=row.reference_date,
        reference_date_label=format_french_date(row.reference_date),
        status=row.status,
        status_label=_status_label(row.status),
        classification_code=row.classification_code,
        classification_code_label=row.classification_code or "Non renseignée",
        remuneration_amount=row.remuneration_amount,
        remuneration_amount_label=_optional_amount_label(row.remuneration_amount),
        applicable_minimum_amount=row.applicable_minimum_amount,
        applicable_minimum_amount_label=_optional_amount_label(row.applicable_minimum_amount),
        shortfall_amount=row.shortfall_amount,
        shortfall_amount_label=format_euro_amount(row.shortfall_amount),
        minimum_source=row.minimum_source,
        minimum_source_label=_source_label(row.minimum_source),
        territory=row.territory,
        territory_label=_territory_label(row.territory),
        failure_reason=row.failure_reason,
        failure_reason_label=_failure_reason_label(row.failure_reason),
        failure_message=row.failure_message,
        failure_message_label=row.failure_message or "",
        issue_code=row.issue_code,
        issue_code_label=row.issue_code or "",
        issue_message=row.issue_message,
        issue_message_label=row.issue_message or "",
    )


def _optional_amount_label(amount: Optional[Decimal]) -> str:
    return format_euro_amount(amount) if amount is not None else "Non disponible"


def _status_label(status: ContractSalaryControlStatus) -> str:
    labels = {
        ContractSalaryControlStatus.COMPLIANT: "Conforme",
        ContractSalaryControlStatus.NON_COMPLIANT: "Non conforme",
        ContractSalaryControlStatus.NOT_EVALUATED: "Non évaluable",
    }
    return labels[status]


def _source_label(source: Optional[ApplicableSalaryMinimumSource]) -> str:
    if source is None:
        return "Non disponible"
    return {
        ApplicableSalaryMinimumSource.CCNS: "CCNS",
        ApplicableSalaryMinimumSource.SMIC: "SMIC",
        ApplicableSalaryMinimumSource.EQUAL: "CCNS et SMIC",
    }[source]


def _territory_label(territory: Optional[SmicTerritory]) -> str:
    if territory is None:
        return "Non renseigné"
    return {
        SmicTerritory.METROPOLITAN_FRANCE: "France métropolitaine",
        SmicTerritory.MAYOTTE: "Mayotte",
    }[territory]


def _failure_reason_label(reason: Optional[ContractSalaryEvaluationFailureReason]) -> str:
    if reason is None:
        return ""
    return {
        ContractSalaryEvaluationFailureReason.CONTRACT_NOT_ACTIVE_ON_REFERENCE_DATE: "Contrat inactif à la date de référence",
        ContractSalaryEvaluationFailureReason.MISSING_CLASSIFICATION: "Classification CCNS manquante",
        ContractSalaryEvaluationFailureReason.MISSING_REMUNERATION: "Rémunération manquante",
        ContractSalaryEvaluationFailureReason.UNSUPPORTED_REMUNERATION_PERIODICITY: "Périodicité de rémunération non prise en charge",
        ContractSalaryEvaluationFailureReason.MISSING_WEEKLY_HOURS: "Durée hebdomadaire manquante",
        ContractSalaryEvaluationFailureReason.MISSING_TERRITORY: "Territoire SMIC manquant",
        ContractSalaryEvaluationFailureReason.ANNUAL_CCNS_MINIMUM_NOT_SUPPORTED: "Minimum CCNS annuel non pris en charge",
    }[reason]


def _presentation_status(result: ContractSalaryControlConsultationApplicationResult) -> ContractSalaryControlPresentationStatus:
    if result.returned_count == 0:
        return ContractSalaryControlPresentationStatus.EMPTY
    if result.filtered_non_compliant_count > 0:
        return ContractSalaryControlPresentationStatus.ERROR
    if result.filtered_not_evaluated_count > 0 or (not result.global_valid and result.filtered_valid):
        return ContractSalaryControlPresentationStatus.WARNING
    return ContractSalaryControlPresentationStatus.SUCCESS


def _summary(result: ContractSalaryControlConsultationApplicationResult, status: ContractSalaryControlPresentationStatus) -> tuple[str, str]:
    if status is ContractSalaryControlPresentationStatus.EMPTY:
        if result.global_valid:
            return "Aucun résultat", "Aucun contrat ne correspond aux critères de consultation."
        return "Aucun résultat filtré", "Aucun contrat ne correspond aux critères, mais le lot global comporte encore des anomalies."
    anomalies = _anomaly_sentence(result.filtered_non_compliant_count, result.filtered_not_evaluated_count)
    if status is ContractSalaryControlPresentationStatus.SUCCESS:
        return "Contrôle salarial conforme", f"Lot globalement conforme : {_contract_count(result.filtered_total_count)} contrôlé{_plural_suffix(result.filtered_total_count)}."
    if status is ContractSalaryControlPresentationStatus.WARNING and result.filtered_valid:
        return "Page filtrée conforme", f"La page filtrée est conforme, mais le lot global comporte encore des anomalies. {anomalies}."
    if status is ContractSalaryControlPresentationStatus.WARNING:
        return "Contrats non évaluables détectés", anomalies + "."
    return "Contrats non conformes détectés", anomalies + "."


def _anomaly_sentence(non_compliant: int, not_evaluated: int) -> str:
    return f"{_non_compliant_count(non_compliant)} ; {_not_evaluated_count(not_evaluated)}"


def _non_compliant_count(count: int) -> str:
    if count == 0:
        return "Aucun contrat non conforme"
    return f"{count} contrat{'s' if count > 1 else ''} non conforme{'s' if count > 1 else ''}"


def _not_evaluated_count(count: int) -> str:
    if count == 0:
        return "aucun contrat non évaluable"
    return f"{count} contrat{'s' if count > 1 else ''} non évaluable{'s' if count > 1 else ''}"


def _contract_count(count: int) -> str:
    if count == 0:
        return "aucun contrat"
    return f"{count} contrat{'s' if count > 1 else ''}"


def _plural_suffix(count: int) -> str:
    return "s" if count > 1 else ""


def _pagination(result: ContractSalaryControlConsultationApplicationResult) -> ContractSalaryControlPaginationViewModel:
    if result.returned_count == 0 or result.offset >= result.filtered_total_count:
        first = last = None
        label = f"Résultats 0 à 0 sur {result.filtered_total_count}"
    else:
        first = result.offset + 1
        last = min(result.offset + result.returned_count, result.filtered_total_count)
        label = f"Résultats {first} à {last} sur {result.filtered_total_count}"
    return ContractSalaryControlPaginationViewModel(
        offset=result.offset,
        limit=result.limit,
        has_previous_page=result.has_previous_page,
        has_next_page=result.has_next_page,
        previous_offset=result.previous_offset,
        next_offset=result.next_offset,
        first_displayed_index=first,
        last_displayed_index=last,
        total_filtered_count=result.filtered_total_count,
        range_label=label,
    )


def _empty_state(result: ContractSalaryControlConsultationApplicationResult, status: ContractSalaryControlPresentationStatus) -> Optional[ContractSalaryControlEmptyStateViewModel]:
    if status is not ContractSalaryControlPresentationStatus.EMPTY:
        return None
    title, message = _summary(result, status)
    return ContractSalaryControlEmptyStateViewModel(title, message)
