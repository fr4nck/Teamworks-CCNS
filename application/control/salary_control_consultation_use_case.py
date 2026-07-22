from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional, Protocol
from uuid import UUID

from domain.contracts.contract import Contract
from domain.contracts.contract_salary_control_consultation import (
    ContractSalaryControlConsultationResult,
    ContractSalaryControlConsultationService,
)
from domain.contracts.contract_salary_control_projection import ContractSalaryControlRow, ContractSalaryControlStatus
from domain.contracts.contract_salary_control_query import (
    ContractSalaryControlQuery,
    ContractSalaryControlSortField,
    SortDirection,
)
from domain.contracts.contract_salary_evaluation import _strict_date, _strict_uuid
from domain.convention.smic import SmicTerritory


class ContractSalaryControlContractProvider(Protocol):
    """Abstraction minimale de sélection des contrats pour la consultation salariale."""

    def list_for_salary_control(
        self,
        *,
        contract_ids: tuple[UUID, ...] = (),
        employee_ids: tuple[UUID, ...] = (),
    ) -> Iterable[Contract]:
        """Retourne le lot de contrats à transmettre tel quel au domaine."""


def _strict_uuid_tuple(value: object, field_name: str) -> tuple[UUID, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} doit être un tuple strict.")
    seen: set[UUID] = set()
    for item in value:
        item = _strict_uuid(item, field_name)
        if item in seen:
            raise ValueError(f"{field_name} ne doit pas contenir de doublons.")
        seen.add(item)
    return value


def _strict_enum_tuple(value: object, field_name: str, item_type: type) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} doit être un tuple strict.")
    seen = set()
    for item in value:
        if type(item) is not item_type:
            raise TypeError(f"{field_name} doit contenir uniquement des {item_type.__name__}.")
        if item in seen:
            raise ValueError(f"{field_name} ne doit pas contenir de doublons.")
        seen.add(item)
    return value


@dataclass(frozen=True, slots=True)
class ConsultContractSalaryControlQuery:
    """Requête applicative de consultation du contrôle salarial CCNS."""

    reference_date: date
    territory: Optional[SmicTerritory] = None
    contract_ids: tuple[UUID, ...] = ()
    employee_ids: tuple[UUID, ...] = ()
    statuses: tuple[ContractSalaryControlStatus, ...] = ()
    search_text: Optional[str] = None
    minimum_shortfall_amount: Optional[Decimal] = None
    maximum_shortfall_amount: Optional[Decimal] = None
    sort_field: ContractSalaryControlSortField = ContractSalaryControlSortField.SOURCE_ORDER
    sort_direction: SortDirection = SortDirection.ASCENDING
    offset: int = 0
    limit: Optional[int] = None

    def __post_init__(self) -> None:
        _strict_date(self.reference_date)
        if self.territory is not None and type(self.territory) is not SmicTerritory:
            raise TypeError("territory doit être None ou un SmicTerritory.")
        _strict_uuid_tuple(self.contract_ids, "contract_ids")
        _strict_uuid_tuple(self.employee_ids, "employee_ids")
        _strict_enum_tuple(self.statuses, "statuses", ContractSalaryControlStatus)
        if self.search_text is not None and type(self.search_text) is not str:
            raise TypeError("search_text doit être None ou une chaîne.")
        for name in ("minimum_shortfall_amount", "maximum_shortfall_amount"):
            value = getattr(self, name)
            if value is not None and type(value) is not Decimal:
                raise TypeError(f"{name} doit être None ou un Decimal strict.")
        if type(self.sort_field) is not ContractSalaryControlSortField:
            raise TypeError("sort_field doit être un ContractSalaryControlSortField.")
        if type(self.sort_direction) is not SortDirection:
            raise TypeError("sort_direction doit être un SortDirection.")
        if type(self.offset) is not int:
            raise TypeError("offset doit être un int strict.")
        if self.limit is not None and type(self.limit) is not int:
            raise TypeError("limit doit être None ou un int strict.")

    def to_domain_query(self) -> ContractSalaryControlQuery:
        return ContractSalaryControlQuery(
            statuses=self.statuses,
            employee_ids=self.employee_ids,
            contract_ids=self.contract_ids,
            minimum_shortfall_amount=self.minimum_shortfall_amount,
            maximum_shortfall_amount=self.maximum_shortfall_amount,
            search_text=self.search_text,
            sort_field=self.sort_field,
            sort_direction=self.sort_direction,
            offset=self.offset,
            limit=self.limit,
        )


@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsultationApplicationResult:
    """Résultat applicatif immuable conservant les valeurs calculées par le domaine."""

    reference_date: date
    rows: tuple[ContractSalaryControlRow, ...]
    global_total_count: int
    global_compliant_count: int
    global_non_compliant_count: int
    global_not_evaluated_count: int
    filtered_total_count: int
    filtered_compliant_count: int
    filtered_non_compliant_count: int
    filtered_not_evaluated_count: int
    returned_count: int
    offset: int
    limit: Optional[int]
    has_previous_page: bool
    has_next_page: bool
    previous_offset: Optional[int]
    next_offset: Optional[int]
    filtered_total_shortfall_amount: Decimal
    global_valid: bool
    filtered_valid: bool

    @classmethod
    def from_domain(
        cls,
        result: ContractSalaryControlConsultationResult,
    ) -> ContractSalaryControlConsultationApplicationResult:
        if type(result) is not ContractSalaryControlConsultationResult:
            raise TypeError("result doit être un ContractSalaryControlConsultationResult.")
        return cls(
            reference_date=result.reference_date,
            rows=result.rows,
            global_total_count=result.control_result.total_count,
            global_compliant_count=result.control_result.compliant_count,
            global_non_compliant_count=result.control_result.non_compliant_count,
            global_not_evaluated_count=result.control_result.not_evaluated_count,
            filtered_total_count=result.total_filtered_count,
            filtered_compliant_count=result.compliant_count,
            filtered_non_compliant_count=result.non_compliant_count,
            filtered_not_evaluated_count=result.not_evaluated_count,
            returned_count=result.returned_count,
            offset=result.offset,
            limit=result.limit,
            has_previous_page=result.has_previous_page,
            has_next_page=result.has_next_page,
            previous_offset=result.previous_offset,
            next_offset=result.next_offset,
            filtered_total_shortfall_amount=result.total_shortfall_amount,
            global_valid=result.control_result.valid,
            filtered_valid=result.valid,
        )


@dataclass(frozen=True, slots=True)
class ConsultContractSalaryControlUseCase:
    """Cas d'usage applicatif stable de consultation du contrôle salarial."""

    contract_provider: ContractSalaryControlContractProvider
    consultation_service: ContractSalaryControlConsultationService

    def __post_init__(self) -> None:
        if not hasattr(self.contract_provider, "list_for_salary_control"):
            raise TypeError("contract_provider doit exposer list_for_salary_control(...).")
        if type(self.consultation_service) is not ContractSalaryControlConsultationService:
            raise TypeError("consultation_service doit être un ContractSalaryControlConsultationService.")

    def execute(self, query: ConsultContractSalaryControlQuery) -> ContractSalaryControlConsultationApplicationResult:
        if type(query) is not ConsultContractSalaryControlQuery:
            raise TypeError("query doit être un ConsultContractSalaryControlQuery.")
        contracts = self.contract_provider.list_for_salary_control(
            contract_ids=query.contract_ids,
            employee_ids=query.employee_ids,
        )
        domain_result = self.consultation_service.consult(
            contracts,
            query.reference_date,
            query.to_domain_query(),
            territory=query.territory,
        )
        return ContractSalaryControlConsultationApplicationResult.from_domain(domain_result)
