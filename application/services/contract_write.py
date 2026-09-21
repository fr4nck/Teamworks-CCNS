"""Frontière d'écriture Contrats indépendante de wx et Qt."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, Protocol

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from application.services.transactional_write import (
    WriteCode,
    WriteResult,
    execute_transactional_delete,
    execute_transactional_insert,
    execute_transactional_update,
    invalid_target_result,
    is_valid_target_id,
)
from domain.contracts.contract_creation_rules import (
    CEEQualification,
    ContractCreationContext,
    ContractCreationRules,
    ConventionCode,
)
from domain.contracts.contract_operation import ContractOperation
from domain.contracts.contract_type import ContractType
from domain.contracts.probation_period import ProbationUnit, probation_calendar_days
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity


ALLOWED_INDICATOR_FIELDS = frozenset(("signature", "due"))
ALLOWED_INDICATOR_VALUES = frozenset(("", "Oui"))
FIXED_TERM_CODES = frozenset(("CDD", "CEE", "APPRENTISSAGE", "STAGE", "SERVICE CIVIQUE"))
CEE_CODES = frozenset(item.value for item in CEEQualification)
SUPPORTED_CREATE_TYPES = frozenset(("CDI", "CDD", "CEE"))


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
    operation_type: Optional[str] = None
    previous_contract_id: Optional[int] = None


@dataclass(frozen=True)
class ContractCreateCommand:
    person_id: int
    contract_type_code: str
    convention_code: str
    ccns_group: Optional[str]
    cee_qualification: Optional[str]
    weekly_hours: Optional[Decimal]
    gross_monthly_salary: Optional[Decimal]
    gross_annual_salary: Optional[Decimal]
    start_date: date
    end_date: Optional[date]
    trial_period_value: int
    trial_period_unit: str
    confirm_no_trial: bool = False
    operation_type: str = ContractOperation.NEW.value
    previous_contract_id: Optional[int] = None


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
    def person_exists(self, person_id: int) -> bool:
        ...

    def available_contract_type_codes(self) -> tuple[str, ...]:
        ...

    def insert_contract(self, command: ContractCreateCommand) -> int:
        ...

    def contract_exists(self, contract_id: int) -> bool:
        ...

    def delete_contract(self, contract_id: int) -> int:
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


def _create_operation(command: ContractCreateCommand) -> ContractOperation | None:
    try:
        return ContractOperation(_normalise_code(command.operation_type))
    except ValueError:
        return None


def _validate_create_operation_shape(
    command: ContractCreateCommand,
    *,
    contract_type: ContractType,
) -> tuple[str, ...]:
    errors: list[str] = []
    operation = _create_operation(command)
    if operation is None:
        return ("Nature de l'opération de contrat inconnue.",)

    if operation is ContractOperation.NEW:
        if command.previous_contract_id is not None:
            errors.append(
                "Un nouveau contrat ne doit pas référencer de contrat précédent."
            )
        return tuple(errors)

    if not is_valid_target_id(command.previous_contract_id):
        errors.append("Le contrat précédent est obligatoire pour cette opération.")

    if operation is ContractOperation.CDD_RENEWAL:
        if contract_type is not ContractType.CDD:
            errors.append("Un renouvellement de CDD doit produire un CDD.")
        if command.trial_period_value != 0:
            errors.append("Un renouvellement de CDD ne doit pas recréer de période d'essai.")
    elif operation is ContractOperation.CDD_TO_CDI:
        if contract_type is not ContractType.CDI:
            errors.append("Un passage CDD vers CDI doit produire un CDI.")

    return tuple(errors)


def _validate_previous_contract(
    command: ContractCreateCommand,
    previous: ContractEditSnapshot | None,
) -> tuple[str, ...]:
    operation = _create_operation(command)
    if operation not in (
        ContractOperation.CDD_RENEWAL,
        ContractOperation.CDD_TO_CDI,
    ):
        return ()

    if previous is None:
        return ("Le contrat précédent sélectionné n'existe plus.",)
    if previous.person_id != command.person_id:
        return ("Le contrat précédent n'appartient pas à la personne sélectionnée.",)
    if _normalise_code(previous.contract_type_code) != ContractType.CDD.value:
        return ("Le contrat précédent doit être un CDD.",)
    if previous.end_date is None:
        return ("Le CDD précédent doit avoir une date de fin exploitable.",)

    expected_start = previous.end_date + timedelta(days=1)
    if command.start_date != expected_start:
        return (
            "Le nouveau contrat doit débuter le lendemain du CDD précédent (%s attendu)."
            % expected_start.isoformat(),
        )
    return ()


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



def validate_contract_create(command: ContractCreateCommand) -> tuple[str, ...]:
    """Valide une création avant toute écriture en base.

    Le rail Qt autorise CDI/CDD sous CCNS et les CEE dont la qualification
    est explicite. Les autres conventions et parcours historiques restent
    hors de ce formulaire tant que leurs règles complètes ne sont pas extraites.
    """

    errors: list[str] = []
    if not is_valid_target_id(command.person_id):
        errors.append("Identifiant historique de la personne invalide.")

    contract_code = _normalise_code(command.contract_type_code)
    if contract_code not in SUPPORTED_CREATE_TYPES:
        errors.append("Ce type de contrat n'est pas encore activé dans la création Qt.")

    if _normalise_code(command.convention_code) != ConventionCode.CCNS.value:
        errors.append("La création Qt initiale est limitée aux contrats CCNS.")

    if errors:
        return tuple(errors)

    try:
        contract_type = ContractType(contract_code)
        convention = ConventionCode(_normalise_code(command.convention_code))
    except ValueError:
        return ("Type de contrat ou convention inconnu.",)

    cee_context_qualification = None
    invalid_cee_qualification = False
    if contract_type is ContractType.CEE and command.cee_qualification:
        try:
            cee_context_qualification = CEEQualification(command.cee_qualification)
        except (TypeError, ValueError):
            invalid_cee_qualification = True

    errors.extend(
        _validate_create_operation_shape(command, contract_type=contract_type)
    )

    context = ContractCreationContext(
        convention=convention,
        contract_type=contract_type,
        classification_code=command.ccns_group,
        cee_qualification=cee_context_qualification,
    )
    if not invalid_cee_qualification:
        errors.extend(ContractCreationRules().validate_context(context))

    edit_equivalent = ContractEditCommand(
        contract_id=1,
        contract_type_code=contract_code,
        convention_code=command.convention_code,
        ccns_group=command.ccns_group,
        cee_qualification=command.cee_qualification,
        weekly_hours=command.weekly_hours,
        gross_monthly_salary=command.gross_monthly_salary,
        gross_annual_salary=command.gross_annual_salary,
        start_date=command.start_date,
        end_date=command.end_date,
        break_date=None,
        modern_fields_supported=True,
    )
    errors.extend(validate_contract_edit(edit_equivalent))

    if type(command.trial_period_value) is not int or command.trial_period_value < 0:
        errors.append("La durée de période d'essai est invalide.")
    try:
        trial_unit = ProbationUnit(command.trial_period_unit)
    except (TypeError, ValueError):
        errors.append("L'unité de période d'essai est invalide.")
        trial_unit = None

    operation = _create_operation(command)
    if contract_type is ContractType.CEE:
        if type(command.trial_period_value) is int and command.trial_period_value != 0:
            errors.append("Un CEE ne doit pas comporter de période d'essai.")
    elif operation is ContractOperation.CDD_RENEWAL:
        pass
    elif (
        type(command.trial_period_value) is int
        and command.trial_period_value == 0
        and not command.confirm_no_trial
    ):
        errors.append(
            "Confirmez explicitement l'absence de période d'essai avant d'enregistrer."
        )

    if not errors and trial_unit is not None:
        try:
            legacy_days = probation_calendar_days(
                start_date=command.start_date,
                value=command.trial_period_value,
                unit=trial_unit,
            )
        except Exception as exc:
            errors.append("La période d'essai ne peut pas être calculée : %s" % exc)
        else:
            if legacy_days > 365:
                errors.append("La période d'essai dépasse la capacité historique de 365 jours.")

    return tuple(errors)


def contract_create_legacy_trial_days(command: ContractCreateCommand) -> int:
    return probation_calendar_days(
        start_date=command.start_date,
        value=command.trial_period_value,
        unit=ProbationUnit(command.trial_period_unit),
    )


def load_contract_creation_types(
    port: ContractWritePort,
) -> WriteResult[tuple[str, ...]]:
    try:
        available = {
            _normalise_code(code)
            for code in port.available_contract_type_codes()
            if _normalise_code(code)
        }
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Lecture des types de contrat impossible : %s" % exc,
        )
    supported = tuple(code for code in ("CDI", "CDD", "CEE") if code in available)
    if not supported:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Aucun type CDI/CDD/CEE exploitable n'est configuré dans la base.",
        )
    return WriteResult(
        ok=True,
        code=WriteCode.OK,
        message="Types de contrat disponibles.",
        value=supported,
    )


def create_contract(
    port: ContractWritePort,
    *,
    command: ContractCreateCommand,
) -> WriteResult[ContractEditSnapshot]:
    errors = validate_contract_create(command)
    if errors:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message=" ".join(errors),
        )

    try:
        if not port.person_exists(command.person_id):
            return WriteResult(
                ok=False,
                code=WriteCode.TARGET_NOT_FOUND,
                message="La personne sélectionnée n'existe plus.",
            )
        available = {
            _normalise_code(code)
            for code in port.available_contract_type_codes()
        }
    except Exception as exc:
        return WriteResult(
            ok=False,
            code=WriteCode.DATABASE_ERROR,
            message="Préflight de création impossible : %s" % exc,
        )

    contract_code = _normalise_code(command.contract_type_code)
    if contract_code not in available:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="Le type de contrat %s n'existe pas dans cette base." % contract_code,
        )

    operation = _create_operation(command)
    if operation in (
        ContractOperation.CDD_RENEWAL,
        ContractOperation.CDD_TO_CDI,
    ):
        try:
            previous = port.read_contract(command.previous_contract_id)
        except Exception as exc:
            return WriteResult(
                ok=False,
                code=WriteCode.DATABASE_ERROR,
                message="Lecture du contrat précédent impossible : %s" % exc,
            )
        operation_errors = _validate_previous_contract(command, previous)
        if operation_errors:
            return WriteResult(
                ok=False,
                code=WriteCode.VALIDATION_ERROR,
                message=" ".join(operation_errors),
            )

    return execute_transactional_insert(
        write=lambda: port.insert_contract(command),
        commit=port.commit,
        rollback=port.rollback,
        readback=lambda contract_id: _readback_contract(port, contract_id),
    )



@dataclass(frozen=True)
class ContractDeleteCommand:
    contract_id: int
    confirmed: bool


def delete_contract(
    port: ContractWritePort,
    *,
    command: ContractDeleteCommand,
) -> WriteResult[bool]:
    """Supprime un contrat uniquement après confirmation explicite."""

    if not is_valid_target_id(command.contract_id):
        return invalid_target_result(command.contract_id)

    if command.confirmed is not True:
        return WriteResult(
            ok=False,
            code=WriteCode.VALIDATION_ERROR,
            message="La suppression du contrat doit être confirmée explicitement.",
            target_id=command.contract_id,
        )

    return execute_transactional_delete(
        target_id=command.contract_id,
        target_exists=lambda: port.contract_exists(command.contract_id),
        write=lambda: port.delete_contract(command.contract_id),
        commit=port.commit,
        rollback=port.rollback,
        readback_exists=lambda: port.read_contract(command.contract_id) is not None,
    )


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


def _readback_contract(port: ContractWritePort, contract_id: int) -> ContractEditSnapshot:
    snapshot = port.read_contract(contract_id)
    if snapshot is None:
        raise LookupError("Contrat introuvable après commit.")
    return snapshot


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
        readback=lambda: _readback_contract(port, command.contract_id),
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
