from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional
from uuid import UUID, uuid4

from domain.contracts.contract import Contract
from domain.contracts.contract_salary_control import ContractSalaryControlResult, ContractSalaryControlService
from domain.contracts.contract_salary_control_projection import (
    ContractSalaryControlProjection,
    ContractSalaryControlRow,
    ContractSalaryControlStatus,
)
from domain.contracts.contract_salary_control_query import ContractSalaryControlPage, ContractSalaryControlQuery, ContractSalaryControlQueryService
from domain.contracts.contract_salary_evaluation import _strict_date, _strict_uuid
from domain.convention.smic import SmicTerritory


@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsultationResult:
    """Résultat composite d'un contrôle salarial suivi d'une consultation paginée."""

    control_result: ContractSalaryControlResult
    page: ContractSalaryControlPage
    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __post_init__(self) -> None:
        if type(self.control_result) is not ContractSalaryControlResult:
            raise TypeError("control_result doit être un ContractSalaryControlResult.")
        if type(self.page) is not ContractSalaryControlPage:
            raise TypeError("page doit être un ContractSalaryControlPage.")
        _strict_uuid(self.id, "id")
        self._validate_consistency()

    def _validate_consistency(self) -> None:
        projection = self.control_result.projection
        if self.page.source_projection is not projection:
            raise ValueError("page.source_projection doit être exactement la projection du contrôle.")
        if self.page.source_projection.reference_date != self.control_result.reference_date:
            raise ValueError("La page et le contrôle doivent porter la même date de référence.")
        if self.page.total_source_count != self.control_result.total_count:
            raise ValueError("total_source_count doit correspondre au total du contrôle.")

        source_identities = {id(row) for row in projection.rows}
        filtered_identities = {id(row) for row in self.page.filtered_rows}
        seen_contract_ids: set[UUID] = set()
        for row in self.page.filtered_rows:
            if id(row) not in source_identities:
                raise ValueError("filtered_rows contient une ligne étrangère à la projection source.")
            if row.contract_id in seen_contract_ids:
                raise ValueError("filtered_rows ne doit pas contenir de doublon de contract_id.")
            seen_contract_ids.add(row.contract_id)
        for row in self.page.rows:
            if id(row) not in filtered_identities:
                raise ValueError("rows contient une ligne étrangère à filtered_rows.")
        if self.page.total_filtered_count != len(self.page.filtered_rows):
            raise ValueError("total_filtered_count doit correspondre à len(filtered_rows).")
        if self.page.returned_count != len(self.page.rows):
            raise ValueError("returned_count doit correspondre à len(rows).")
        expected_rows = self.page.filtered_rows[self.page.offset:]
        if self.page.limit is not None:
            expected_rows = expected_rows[: self.page.limit]
        if self.page.rows != expected_rows:
            raise ValueError("rows doit respecter l'ordre de filtered_rows après pagination.")

    @property
    def reference_date(self) -> date:
        return self.control_result.reference_date

    @property
    def query(self) -> ContractSalaryControlQuery:
        return self.page.query

    @property
    def source_projection(self) -> ContractSalaryControlProjection:
        return self.page.source_projection

    @property
    def filtered_rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.page.filtered_rows

    @property
    def rows(self) -> tuple[ContractSalaryControlRow, ...]:
        return self.page.rows

    @property
    def total_source_count(self) -> int:
        return self.page.total_source_count

    @property
    def total_filtered_count(self) -> int:
        return self.page.total_filtered_count

    @property
    def returned_count(self) -> int:
        return self.page.returned_count

    @property
    def offset(self) -> int:
        return self.page.offset

    @property
    def limit(self) -> Optional[int]:
        return self.page.limit

    @property
    def has_previous_page(self) -> bool:
        return self.page.has_previous_page

    @property
    def has_next_page(self) -> bool:
        return self.page.has_next_page

    @property
    def next_offset(self) -> Optional[int]:
        return self.page.next_offset

    @property
    def previous_offset(self) -> Optional[int]:
        return self.page.previous_offset

    @property
    def compliant_count(self) -> int:
        return self.page.compliant_count

    @property
    def non_compliant_count(self) -> int:
        return self.page.non_compliant_count

    @property
    def not_evaluated_count(self) -> int:
        return self.page.not_evaluated_count

    @property
    def total_shortfall_amount(self) -> Decimal:
        return self.page.total_shortfall_amount

    @property
    def valid(self) -> bool:
        return self.page.valid

    @property
    def is_empty(self) -> bool:
        return self.page.is_empty

    def row_for_contract(self, contract_id: UUID) -> Optional[ContractSalaryControlRow]:
        return self.page.row_for_contract(contract_id)

    def rows_for_employee(self, employee_id: UUID) -> tuple[ContractSalaryControlRow, ...]:
        return self.page.rows_for_employee(employee_id)

    def rows_for_status(self, status: ContractSalaryControlStatus) -> tuple[ContractSalaryControlRow, ...]:
        return self.page.rows_for_status(status)


@dataclass(frozen=True, slots=True)
class ContractSalaryControlConsultationService:
    contract_salary_control_service: ContractSalaryControlService
    contract_salary_control_query_service: ContractSalaryControlQueryService

    def __post_init__(self) -> None:
        if type(self.contract_salary_control_service) is not ContractSalaryControlService:
            raise TypeError("contract_salary_control_service doit être un ContractSalaryControlService.")
        if type(self.contract_salary_control_query_service) is not ContractSalaryControlQueryService:
            raise TypeError("contract_salary_control_query_service doit être un ContractSalaryControlQueryService.")

    def consult(
        self,
        contracts: Iterable[Contract],
        reference_date: date,
        query: ContractSalaryControlQuery,
        *,
        territory: Optional[SmicTerritory] = None,
    ) -> ContractSalaryControlConsultationResult:
        _strict_date(reference_date)
        if type(query) is not ContractSalaryControlQuery:
            raise TypeError("query doit être un ContractSalaryControlQuery.")
        if territory is not None and type(territory) is not SmicTerritory:
            raise TypeError("territory doit être un SmicTerritory.")
        control_result = self.contract_salary_control_service.control(contracts, reference_date, territory=territory)
        if type(control_result) is not ContractSalaryControlResult:
            raise TypeError("control_result doit être un ContractSalaryControlResult.")
        page = self.contract_salary_control_query_service.execute(control_result.projection, query)
        if type(page) is not ContractSalaryControlPage:
            raise TypeError("page doit être un ContractSalaryControlPage.")
        return ContractSalaryControlConsultationResult(control_result, page)
