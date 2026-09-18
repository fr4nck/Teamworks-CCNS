"""Frontière d'écriture Contrats indépendante de wx et Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, Protocol

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from application.services.transactional_write import (
    WriteCode,
    WriteResult,
    execute_transactional_update,
    invalid_target_result,
    is_valid_target_id,
)
from domain.contracts.contract_creation_rules import CEEQualification
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity


ALLOWED_INDICATOR_FIELDS = frozenset(("signature", "due"))
ALLOWED_INDICATOR_VALUES = frozenset(("", "Oui"))
FIXED_TERM_CODES = frozenset(("CDD", "CEE", "APPRENTISSAGE", "STAGE", "SERVICE CIVIQUE"))
CEE_CODES = frozenset(item.value for item in CEEQualification)


@dataclass(frozen=True)
class ContractEditSnapshot:
    contract_id: int
    person_id: int
    contract_type_code: str
    contract_type_label: str
    convention_code: Optional[str]
    ccns_group: Optional[str]
    cee_qualification: Optional[str]
    weekly_hours: Optional[Decimal]
    gross_monthly_salary: Optional[Decimal]
    gross_annual_salary: Optional[Decimal]
    start_date: date
    end_date: Optional[date]
    break_date: Optional[date]
    modern_fields_supported: bool


@dataclass(frozen=True)
class ContractEditCommand:
    contract_id: int
    contract_type_code: str
    convention_code: Optional[str]
    ccns_group: Optional[str]
    cee_qualification: Optional[str]
    weekly_hours: Optional[Decimal]
    gross_monthly_salary: Optional[Decimal]
    gross_annual_salary: Optional[Decimal]
    start_date: date
    end_date: Optional[date]
    break_date: Optional[date]
    modern_fields_supported: bool


class ContractWritePort(Protocol):
    def contract_exists(self, contract_id: int) -> bool:
        ...

    def update_indicator(self, contract_id: int, field: str, value: str) -> int:
        ...

    def read_indicator(self, contract_id: int, field: str) -> str:
        ...

    def read_contract(self, contract_id: int) -> ContractEditSnapshot | None:
        ...

    def update_contract(self, command: ContractEditCommand) -> int:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...


def _normalise_code(value: object) -> str:
    return str(value or "").strip().upper()


def _is_cee(command: ContractEditCommand) -> bool:
    return _normalise_code(command.contract_type_code) == "CEE"


def validate_contract_edit(
    command: ContractEditCommand,
    *,
    original: ContractEditSnapshot | None = None,
) -> tuple[str, ...]:
    """Valide le noyau métier modifiable avant toute écriture SQL."""

    errors: list[str] = []
    if not is_valid_target_id(command.contract_id):
        return ("Identifiant historique du contrat invalide.",)
    if type(command.start_date) is not date:
        return ("La date de début est obligatoire.",)
    if command.end_date is not None and type(command.end_date) is not date:
        errors.append("La date de fin est invalide.")
    if command.break_date is not None and type(command.break_date) is not date:
        errors.append("La date de rupture est invalide.")
    if errors:
        return tuple(errors)

    contract_code = _normalise_code(command.contract_type_code)
    if contract_code in FIXED_TERM_CODES and command.end_date is None:
        errors.append("Une date de fin est obligatoire pour ce type de contrat.")
    if command.end_date is not None and command.end_date < command.start_date:
        errors.append("La date de fin est antérieure à la date de début.")
    if command.break_date is not None and command.break_date < command.start_date:
        errors.append("La date de rupture est antérieure à la date de début.")
    if (
        command.break_date is not None
        and command.end_date is not None
        and command.break_date >= command.end_date
    ):
        errors.append("La date de rupture doit être antérieure à la date de fin.")

    if not command.modern_fields_supported:
        return tuple(errors)

    if _is_cee(command):
        legacy_missing_qualification = bool(
            original is not None
            and not original.cee_qualification
            and not command.cee_qualification
        )
        if not command.cee_qualification and not legacy_missing_qualification:
            errors.append("La qualification ou le statut CEE est obligatoire.")
        elif command.cee_qualification and command.cee_qualification not in CEE_CODES:
            errors.append("La qualification CEE est inconnue.")
        if command.ccns_group:
            errors.append("Un CEE ne doit pas porter de groupe CCNS.")
        return tuple(errors)

    if _normalise_code(command.convention_code) != "CCNS":
        return tuple(errors)

    group = _normalise_code(command.ccns_group)
    if not group:
        errors.append("Le groupe CCNS est obligatoire.")
        return tuple(errors)
    if type(command.weekly_hours) is not Decimal or command.weekly_hours <= Decimal("0"):
        errors.append("La durée hebdomadaire doit être strictement positive.")
        return tuple(errors)

    presenter = CCNSContractCompliancePresenter()
    try:
        choice = next(
            (
                item
                for item in presenter.group_choices(command.start_date)
                if item.code == group
            ),
            None,
        )
    except Exception:
        choice = None
    if choice is None:
        errors.append("Le groupe CCNS n'est pas applicable à la date de début.")
        return tuple(errors)

    if choice.periodicity is SalaryMinimumPeriodicity.MONTHLY:
        salary = command.gross_monthly_salary
        if type(salary) is not Decimal or salary <= Decimal("0"):
            errors.append("La rémunération brute mensuelle est obligatoire.")
            return tuple(errors)
        try:
            preview = presenter.evaluate_monthly(
                group_code=group,
                reference_date=command.start_date,
                weekly_hours=command.weekly_hours,
                remuneration_amount=salary,
            )
        except Exception as exc:
            errors.append("Le contrôle CCNS/SMIC n'a pas pu être calculé : %s" % exc)
            return tuple(errors)
        if not preview.compliant:
            errors.append(
                "La rémunération saisie est inférieure au minimum CCNS/SMIC applicable."
            )
    else:
        salary = command.gross_annual_salary
        if type(salary) is not Decimal or salary <= Decimal("0"):
            errors.append("La rémunération annuelle de référence est obligatoire.")
        elif command.weekly_hours == Decimal("35") and salary < choice.minimum_amount:
            errors.append(
                "La rémunération annuelle est inférieure au minimum CCNS du groupe."
            )

    return tuple(errors)


def contract_edit_has_changes(
    original: ContractEditSnapshot,
    command: ContractEditCommand,
) -> bool:
    comparable = (
        "convention_code",
        "ccns_group",
        "cee_qualification",
        "weekly_hours",
        "gross_monthly_salary",
        "gross_annual_salary",
        "start_date",
        "end_date",
        "break_date",
    )
    return any(getattr(original, name) != getattr(command, name) for name in comparable)


def load_contract_for_edit(
    port: ContractWritePort,
    *,
    contract_id: object,
) -> WriteResult[ContractEditSnapshot]:
    if not is_valid_target_id(contract_id):
        return invalid_target_result(contract_id)
    try:
        snapshot = port.read_contract(contract_id)
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Lecture du contrat impossible : %s" % exc,
            target_id=contract_id,
        )
    if snapshot is None:
        return WriteResult(
            ok=False,
            code=WriteCode.TARGET_NOT_FOUND,
            message="Le contrat sélectionné n'existe plus.",
            target_id=contract_id,
        )
    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Contrat chargé.",
        target_id=contract_id,
        value=snapshot,
        committed=False,
    )


def update_contract(
    port: ContractWritePort,
    *,
    command: ContractEditCommand,
) -> WriteResult[ContractEditSnapshot]:
    if not is_valid_target_id(command.contract_id):
        return invalid_target_result(command.contract_id)

    loaded = load_contract_for_edit(port, contract_id=command.contract_id)
    if not loaded.ok or loaded.value is None:
        return loaded
    original = loaded.value

    errors = validate_contract_edit(command, original=original)
    if errors:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=" ".join(errors),
            target_id=command.contract_id,
        )

    if not contract_edit_has_changes(original, command):
        return WriteResult(
            ok=True,
            code=WriteCode.OK,
            message="Aucune modification à enregistrer.",
            target_id=command.contract_id,
            value=original,
            committed=False,
        )

    return execute_transactional_update(
        target_id=command.contract_id,
        target_exists=lambda: port.contract_exists(command.contract_id),
        write=lambda: port.update_contract(command),
        commit=port.commit,
        rollback=port.rollback,
        readback=lambda: port.read_contract(command.contract_id),
    )


def update_contract_indicator(
    port: ContractWritePort,
    *,
    contract_id: object,
    field: str,
    value: str,
) -> WriteResult[str]:
    """Met à jour un indicateur historique du contrat par ID stable."""

    if not is_valid_target_id(contract_id):
        return invalid_target_result(contract_id)

    if field not in ALLOWED_INDICATOR_FIELDS:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Indicateur contrat non autorisé : %s." % field,
            target_id=contract_id,
        )

    if value not in ALLOWED_INDICATOR_VALUES:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Valeur d'indicateur contrat invalide.",
            target_id=contract_id,
        )

    if port is None:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Aucun adaptateur d'écriture disponible.",
            target_id=contract_id,
        )

    return execute_transactional_update(
        target_id=contract_id,
        target_exists=lambda: port.contract_exists(contract_id),
        write=lambda: port.update_indicator(contract_id, field, value),
        commit=port.commit,
        rollback=port.rollback,
        readback=lambda: port.read_indicator(contract_id, field),
    )
