from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional, Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

from application.control import ContractSalaryControlContractProvider
from domain.contracts.contract import Contract
from domain.contracts.contract_type import ContractType
from domain.repositories.ccns_data import CcnsContratRecord, CcnsDataReaderProtocol
from domain.convention.classification import CCNSClassification
from infrastructure.persistence.teamworks_contract_conversions import as_date, map_contract_type, map_employment_regime, map_time_organization

HISTORICAL_FIXED_TERM_WITHOUT_END_DATE_REASON = "CONTRAT_A_DUREE_DETERMINEE_SANS_DATE_FIN"
_CONTRACT_NAMESPACE = uuid5(NAMESPACE_URL, "teamworks-ccns:legacy-contract")
_EMPLOYEE_NAMESPACE = uuid5(NAMESPACE_URL, "teamworks-ccns:legacy-employee")
_FIXED_TERM_TYPES = frozenset(
    {
        ContractType.CDD,
        ContractType.CEE,
        ContractType.APPRENTICESHIP,
        ContractType.INTERNSHIP,
        ContractType.CIVIC_SERVICE,
    }
)


@dataclass(frozen=True, slots=True)
class TeamworksContractSalaryControlProvider(ContractSalaryControlContractProvider):
    """Adaptateur des contrats Teamworks réels vers le contrôle salarial."""

    data_reader: CcnsDataReaderProtocol
    records: Optional[Sequence[CcnsContratRecord]] = None

    def __post_init__(self) -> None:
        if not hasattr(self.data_reader, "lire_contrats"):
            raise TypeError("data_reader doit exposer lire_contrats(...).")

    def list_for_salary_control(
        self,
        *,
        contract_ids: tuple[UUID, ...] = (),
        employee_ids: tuple[UUID, ...] = (),
    ) -> Iterable[Contract]:
        _strict_uuid_tuple(contract_ids, "contract_ids")
        _strict_uuid_tuple(employee_ids, "employee_ids")
        selected_contract_ids = set(contract_ids)
        selected_employee_ids = set(employee_ids)
        result: list[Contract] = []
        seen_contract_ids: set[UUID] = set()
        records = self.records if self.records is not None else self.data_reader.lire_contrats()
        for record in records:
            contract = contract_from_ccns_record(record)
            contract_id = _legacy_contract_uuid(record.IDcontrat)
            employee_id = _legacy_employee_uuid(record.IDpersonne)
            if contract_ids and contract_id not in selected_contract_ids:
                continue
            if employee_ids and employee_id not in selected_employee_ids:
                continue
            if contract_id in seen_contract_ids:
                continue
            result.append(contract)
            seen_contract_ids.add(contract_id)
        return result


def legacy_contract_uuid(IDcontrat: int) -> UUID:
    return _legacy_contract_uuid(IDcontrat)


def legacy_employee_uuid(IDpersonne: int) -> UUID:
    return _legacy_employee_uuid(IDpersonne)


def contract_from_ccns_record(record: CcnsContratRecord) -> Contract:
    if type(record) is not CcnsContratRecord:
        raise TypeError("record doit être un CcnsContratRecord strict.")
    contract_type = map_contract_type(record.type_contrat)
    failure_reason: Optional[str] = None
    end_date = as_date(record.date_fin)
    if contract_type in _FIXED_TERM_TYPES and end_date is None:
        failure_reason = HISTORICAL_FIXED_TERM_WITHOUT_END_DATE_REASON
    classification = _classification(record.classification)
    return Contract(
        id=_legacy_contract_uuid(record.IDcontrat),
        person_id=str(_legacy_employee_uuid(record.IDpersonne)),
        contract_type=contract_type,
        employment_regime=map_employment_regime(contract_type),
        time_organization=map_time_organization(contract_type),
        start_date=as_date(record.date_debut),
        end_date=end_date,
        weekly_reference_hours=float(record.temps_hebdo) if record.temps_hebdo is not None else None,
        ccns_classification_code=record.classification,
        ccns_classification=classification,
        base_salary_amount=float(record.salaire_base) if record.salaire_base is not None else None,
        monthly_gross_salary_amount=_decimal_or_none(record.salaire_base),
        weekly_hours=_decimal_or_none(record.temps_hebdo),
        salary_unit="monthly",
        contract_status="legacy",
        work_ratio=1.0,
        legacy_salary_control_failure_reason=failure_reason,
    )


def _classification(code: Optional[str]) -> Optional[CCNSClassification]:
    if not code or not code.strip():
        return None
    cleaned = code.strip()
    return CCNSClassification(code=cleaned, label=cleaned)


def _decimal_or_none(value: Optional[float]) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _legacy_contract_uuid(IDcontrat: int) -> UUID:
    return uuid5(_CONTRACT_NAMESPACE, str(int(IDcontrat)))


def _legacy_employee_uuid(IDpersonne: int) -> UUID:
    return uuid5(_EMPLOYEE_NAMESPACE, str(int(IDpersonne)))


def _strict_uuid_tuple(value: object, field_name: str) -> tuple[UUID, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} doit être un tuple strict.")
    seen: set[UUID] = set()
    for item in value:
        if type(item) is not UUID:
            raise TypeError(f"{field_name} doit contenir uniquement des UUID stricts.")
        if item in seen:
            raise ValueError(f"{field_name} ne doit pas contenir de doublons.")
        seen.add(item)
    return value
